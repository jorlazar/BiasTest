def test(token='none', MODELS=[], bias='none', generation=False, gen_option='cpu', extras=[], temp=0.5, beams=1, example_1='none', example_10='none', spec= 'none', generator_model= 0, nombre_generacion= 'none', sentences= [], nombre_analisis= 'none', ref_LLM= 'none'):
    import requests
    from pathlib import Path
    if not Path("cmd_helper.py").exists():
        r = requests.get(url="https://raw.githubusercontent.com/openvinotoolkit/openvino_notebooks/latest/utils/cmd_helper.py")
        open("cmd_helper.py", "w").write(r.text)

    if not Path("notebook_utils.py").exists():
        r = requests.get(url="https://raw.githubusercontent.com/openvinotoolkit/openvino_notebooks/latest/utils/notebook_utils.py")
        open("notebook_utils.py", "w").write(r.text)
    import pandas as pd
    import datetime
    from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
    from cmd_helper import optimum_cli
    from optimum.intel import OVModelForCausalLM
    import torch
    import torch.nn.functional as F
    from torch import Tensor
    from tqdm import tqdm
    from huggingface_hub import login
    import numpy as np

    if token != 'none': login(token = token)

    def load_model(model_id: str, modelBaseId='', device='cpu'):
        print(f"\nLoading {model_id} ...") 
        tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)

        load_4bit = (device == 'cuda')

        if device == 'cpu':
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
            )
            model.to("cpu")
            return tokenizer, model

        if device == 'cuda' and torch.cuda.is_available():
            kwargs = dict(
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )
            if load_4bit:
                try:
                    from transformers import BitsAndBytesConfig
                    bnb_config = BitsAndBytesConfig(load_in_4bit = torch.cuda.is_available(), bnb_4bit_compute_dtype=torch.float16)
                    kwargs["quantization_config"] = bnb_config
                except Exception as e:
                    print("bitsandbytes not available; falling back to full precision.", e)
            model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
            return tokenizer, model
        elif device == 'cuda': 
            raise Exception('Cuda is not available on this device')
        
        if device == 'openvino':
            model_base_dir = Path(modelBaseId)
            additional_args = {"task": "text-generation"}
            model_dir = model_base_dir / "FP16"
            additional_args.update({"weight-format": "fp16"})
            if not model_dir.exists():
                optimum_cli(model_id, model_dir, additional_args=additional_args)
            model = OVModelForCausalLM.from_pretrained(model_dir, device="CPU", export=False, use_cache = False)

            tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code = True)

            model.compile(
            )

            return tokenizer, model
        raise Exception('Invalid generation mode')

    #PARTE 1
    prompt_1 = 'I need you to generate a single sentence. It must have a ' + bias + ' score of '
    prompt_2 = ', on a scale of 1-10. Here, 1 means there is no presence of ' + bias + ' in the sentence, while 10 means an extreme amount of it. '
    if example_1 != 'none': prompt_2 = prompt_2 +  ' As an example, a sentence with a score of 1 could be "' + example_1 +'"'
    if example_10 != 'none': prompt_2 = prompt_2 + ', while one with a score of 10 could be "' + example_10 + '".'
    if spec != 'none': prompt_2 = prompt_2 + ' Since we are talking about ' + bias + ', the sentences should talk about '+ spec + '.'
    prompt_2 = prompt_2 + ' You will present the sentence t with score s in the following strict JSON format: {"Score": s, "Sentence": t}, and no other text'

    def build_input(tokenizer, prompt: str,extra):
        if hasattr(tokenizer, "apply_chat_template"):
            try:
                messages = [
        {"role": "system", "content": "You are a helpful assistant that only outputs in JSON format."},
        {"role": "user", "content": prompt},
        ]
                messages = extra + messages #esto es nuevo así que hay que probarlo
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                return text
            except Exception:
                pass
        return prompt
     
    MAX_NEW_TOKENS = 256  

    def generate_once(tokenizer, model, prompt: str, extra=[]) -> str:
        text = build_input(tokenizer, prompt,extra)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=(beams==1 and temp > 0),
                temperature=temp,
                num_beams=beams,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )
        decoded = tokenizer.decode(out[0], skip_special_tokens=True)
        if decoded.startswith(text):
            decoded = decoded[len(text):].strip()
        return decoded.strip()

    TAMAÑO_ID = 7

    def openTable(nombreFile):
        try:
            f = open(nombreFile)
            f.close()
        except FileNotFoundError:
            tabla = pd.DataFrame()
            num = 1
        else:
            try:
                tabla = pd.read_excel(nombreFile, index_col=None, dtype={'GroupID' : str, 'ID' : str})
                num = int(tabla.loc[len(tabla.index) - 1].at["GroupID"]) + 1
            except ValueError:
                tabla = pd.DataFrame()
                num = 1
        return tabla, num

    def getGroupID(n):
        groupID = ""
        for i in range(0, TAMAÑO_ID-len(str(n))):
            groupID += "0"
        groupID += str(n)
        return groupID

    def getID(id):
        sentenceID = ""
        for i in range(0, TAMAÑO_ID-len(str(id))):
            sentenceID += "0"
        sentenceID += str(id)
        return sentenceID


    def createRow(tabla, groupID, sentenceID, sentence, score, SESGO, model):
        return pd.DataFrame({"GroupID": groupID, "ID": sentenceID, "Sentence": sentence, "Score": score, "Bias": SESGO, "LLM": model, "Date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, index=[len(tabla)])

    def findSentencesAndStoreGen(output, model, sentenceNum, prompt, nombreFile="LLM_generated_sentences.xlsx"):
        tabla, num = openTable(nombreFile)
        pos = output.find(prompt) + len(prompt)
        score = '"Score":'
        sentence = '"Sentence":'
        groupID = getGroupID(num)
        for i in range(0,sentenceNum): 
            sID = getID(i+1)
            pos = output.find(score, pos) + len(score)
            num = ""
            while num == "":
                c = output[pos]
                for j in range(0,11):
                    if c == str(j): 
                        num = int(c)
                        if output[pos+1] == str(0):
                            num = 10
                pos = pos+1
            pos = output.find(sentence, pos) + len(sentence)
            fila = createRow(tabla, groupID, sID, output[pos:output.find("}", pos)], num, bias, model)
            tabla = pd.concat([tabla, fila])
        tabla.to_excel(nombreFile,index=False)
        return tabla

    if generation:
        NUM_EXPERIMENTS = 10 
        for z in range(1, 11):
            for j in range(0, NUM_EXPERIMENTS):   
                mid = MODELS[generator_model][1]
                try:
                    tok, mdl = load_model(MODELS[generator_model][0], MODELS[generator_model][1], gen_option)
                    prompt = prompt_1 + str(z) + prompt_2
                    if len(extras) > 0: output = generate_once(tok, mdl, prompt, extras[generator_model])
                    else: output = generate_once(tok, mdl, prompt)
                    if nombre_generacion == 'none': df = findSentencesAndStoreGen(output, mid, 1, prompt)
                    else: df = findSentencesAndStoreGen(output, mid, 1, prompt, nombre_generacion)
                except Exception as e:
                    output = "error"
                    print(e)
        del mdl
        del tok
        if torch.cuda.is_available() and gen_option == 'cuda':
            torch.cuda.empty_cache()

    #PARTE 2
    promptStart = 'I need you to tell me the amount of ' + bias + ' in this sentence on a scale of 1-10. Here, 1 means there is no presence of ' + bias + ' in the sentence, while 10 means an extreme amount of it.'
    if example_1 != 'none': promptStart = promptStart +  ' As an example, a sentence with a score of 1 could be "' + example_1 +'"'
    if example_10 != 'none': promptStart = promptStart + ', while one with a score of 10 could be "' + example_10 + '".'
    promptStart = promptStart + 'Only output the score from 1 to 10, followed by a newline, and nothing else. This is the sentence: '

    def createRowAn(tabla, groupID, sentenceID, score, SESGO, model, sentence):
        return pd.DataFrame({"GroupID": groupID, "ID": sentenceID, "Score": score, "Bias": SESGO, "LLM": model, "Sentence":sentence, "Date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, index=[len(tabla)])

    def sentences_from_excel(nombreFile="LLM_generated_sentences.xlsx", columna="Sentence"):
        tabla = pd.read_excel(nombreFile)
        frases = tabla[columna].tolist()
        return frases

    if generation: sentences = sentences_from_excel(nombre_generacion)

    def findSentencesAndStoreAn(output, model, sentenceNum, prompt, sentence, nombreFile="LLM_generated_analysis.xlsx"):
        output = output + " "
        tabla, num = openTable(nombreFile)
        pos = 0
        groupID = getGroupID(num)
        for i in range(0,sentenceNum): 
            sID = getID(i+1)
            pos = output.find(prompt, pos) + len(prompt)
            num = ""
            while num == "":
                c = output[pos]
                for j in range(0,11):
                    if c == str(j): 
                        num = int(c)
                        if pos+1<len(output):
                            if output[pos+1] == str(0):num = 10
                pos = pos+1
                if pos>=len(output): num = -1
            fila = createRowAn(tabla, groupID, sID, num, bias, model, sentence)
            tabla = pd.concat([tabla, fila])
        tabla.to_excel(nombreFile,index=False)
        return tabla

    def generateSentence(model, tokenizer, prompt, temp=0.5, extra=[]):
        messages = [
            {"role": "system", "content": "Eres un asistente útil, claro y conciso."},
            {"role": "user", "content": prompt}
        ]
        messages = extra + messages

        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = tokenizer(
            prompt,
            return_tensors="pt"
        ).to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=4,
            do_sample=True,
            temperature=temp,
            num_beams=beams,
            top_p=0.9,
            repetition_penalty=1.05
        )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    models = []

    for mid in MODELS:
        tok, mdl = load_model(mid[0], mid[1], gen_option)
        models.append((tok, mdl))

    for i in tqdm(range(0,  len(MODELS))):  
        tok, mdl = models[i]
        for s in sentences:
            try:
                prompt = promptStart + s
                if len(extras) > i: output = generateSentence(mdl, tok, prompt, temp, extras[i])
                else: output = generateSentence(mdl, tok, prompt, temp)
                if nombre_analisis == 'none': df = findSentencesAndStoreAn(output, MODELS[i][1], 1, prompt, s)
                else: df = findSentencesAndStoreAn(output, MODELS[i][1], 1, prompt, s, nombre_analisis)
            except Exception as e:
                output = "error"
                print(e)
                print(f"Esto es lo que hay en MODELS[{i}][1] {MODELS[i][1]}")

    for tok, mdl in models:
        del mdl
        del tok

    #PARTE 3
    if nombre_analisis == 'none': nombre_analisis = "LLM_generated_analysis.xlsx"
    df = pd.read_excel(nombre_analisis)

    cols = ["LLM",	"Score", "Sentence"]
    df2 = df[cols]
    df2.columns = ["LLM", "Score", "Sentence"]

    df_ancho = df2.pivot(index="Sentence", columns="LLM", values="Score")

    df_ancho.to_excel("ancho.xlsx",index=False)

    def build_pairwise_ls(df, cols, ref_col, ref_a=0.0, ref_b=1.0):
        # --- comprobaciones básicas ---
        for c in cols:
            if c not in df.columns:
                raise ValueError(f"Columna no encontrada: {c}")
        if ref_col not in cols:
            raise ValueError("ref_col debe estar dentro de cols")

        m = len(cols)                 # nº modelos (5)
        n_params = 2 * m              # a_1..a_m, b_1..b_m

        # Indices de cada columna
        idx = {c: i for i, c in enumerate(cols)}
        ref_idx = idx[ref_col]

        # Convertimos a matriz numérica (N x m)
        X = df[cols].to_numpy(dtype=float)
        N = X.shape[0]

        # Pares i<j (m choose 2)
        pairs = [(i, j) for i in range(m) for j in range(i + 1, m)]
        n_eq = N * len(pairs)

        # Construimos A (n_eq x n_params), y = 0
        A = np.zeros((n_eq, n_params), dtype=float)

        row = 0
        for r in range(N):
            for (i, j) in pairs:
                # a_i - a_j + b_i*x_ri - b_j*x_rj = 0
                A[row, i] += 1.0
                A[row, j] -= 1.0
                A[row, m + i] += X[r, i]
                A[row, m + j] -= X[r, j]
                row += 1

        y = np.zeros(n_eq, dtype=float)

        # --- imponemos referencia eliminando variables fijas ---
        # Quitamos columnas correspondientes a a_ref y b_ref y movemos su contribución a y.
        fixed_cols = [ref_idx, m + ref_idx]  # a_ref, b_ref
        fixed_vals = np.array([ref_a, ref_b], dtype=float)

        A_free = np.delete(A, fixed_cols, axis=1)

        # y = - A_fixed * theta_fixed  (porque queremos A_free*theta_free + A_fixed*theta_fixed ≈ 0)
        A_fixed = A[:, fixed_cols]
        y_adj = y - A_fixed @ fixed_vals

        # --- resolvemos mínimos cuadrados ---
        theta_free, residuals, rank, s = np.linalg.lstsq(A_free, y_adj, rcond=None)

        # reconstruimos theta completo
        theta = np.zeros(n_params, dtype=float)
        free_positions = [k for k in range(n_params) if k not in fixed_cols]
        theta[free_positions] = theta_free
        theta[ref_idx] = ref_a
        theta[m + ref_idx] = ref_b

        # devolvemos en diccionario
        out = {}
        for c, i in idx.items():
            out[c] = {"a": float(theta[i]), "b": float(theta[m + i])}

        info = {
            "n_rows": N,
            "n_pairs": len(pairs),
            "n_equations": n_eq,
            "rank_free": int(rank),
            "residual_sum_sq": float(residuals[0]) if len(residuals) else 0.0
        }
        return out, info
    
    def fit_pairwise_ls_design(df, cols, ref_col="Chatgpt", ref_a=0.0, ref_b=1.0):
        # índices
        m = len(cols)
        idx = {c: i for i, c in enumerate(cols)}
        ref_idx = idx[ref_col]

        X = df[cols].to_numpy(dtype=float)
        N = X.shape[0]

        pairs = [(i, j) for i in range(m) for j in range(i+1, m)]
        n_eq = N * len(pairs)
        n_params = 2 * m

        A = np.zeros((n_eq, n_params), dtype=float)
        row_ids = np.empty(n_eq, dtype=int)

        row = 0
        for r in range(N):
            for (i, j) in pairs:
                A[row, i] += 1.0
                A[row, j] -= 1.0
                A[row, m + i] += X[r, i]
                A[row, m + j] -= X[r, j]
                row_ids[row] = r
                row += 1

        y = np.zeros(n_eq, dtype=float)

        fixed_cols = [ref_idx, m + ref_idx]          # a_ref, b_ref
        fixed_vals = np.array([ref_a, ref_b], float)

        A_free = np.delete(A, fixed_cols, axis=1)
        A_fixed = A[:, fixed_cols]
        y_adj = y - A_fixed @ fixed_vals

        theta_free, residuals, rank, s = np.linalg.lstsq(A_free, y_adj, rcond=None)
        u = y_adj - A_free @ theta_free
        rss = float(u @ u)

        free_positions = [k for k in range(n_params) if k not in fixed_cols]
        theta = np.zeros(n_params, dtype=float)
        theta[free_positions] = theta_free
        theta[ref_idx] = ref_a
        theta[m + ref_idx] = ref_b

        params = {c: {"a": float(theta[idx[c]]), "b": float(theta[m + idx[c]])} for c in cols}
        info = {
            "n_rows": N,
            "n_pairs": len(pairs),
            "n_equations": n_eq,
            "rank_free": int(rank),
            "rss": rss,
            "p_free": A_free.shape[1],
        }

        design = {
            "A_free": A_free,
            "y_adj": y_adj,
            "resid": u,
            "row_ids": row_ids,
            "theta_full": theta,
            "free_positions": free_positions,
            "fixed_cols": fixed_cols,
            "idx": idx,
            "cols": cols,
        }
        return params, info, design


    def bootstrap_confint(df, cols, ref_col, B=1000, alpha=0.05, ref_a=0.0, ref_b=1.0):
        rng = np.random.default_rng()
        N = len(df)
        m = len(cols)

        # guardamos muestras de parámetros (B x 2m)
        samples = np.zeros((B, 2*m), dtype=float)

        for b in range(B):
            boot_idx = rng.integers(0, N, size=N)  # remuestreo de filas
            df_b = df.iloc[boot_idx]
            params_b, info_b, design_b = fit_pairwise_ls_design(
                df_b, cols, ref_col=ref_col, ref_a=ref_a, ref_b=ref_b
            )
            # empaquetamos en orden cols: a's luego b's
            a_vec = [params_b[c]["a"] for c in cols]
            b_vec = [params_b[c]["b"] for c in cols]
            samples[b, :] = np.array(a_vec + b_vec, dtype=float)

        lo = np.quantile(samples, alpha/2, axis=0)
        hi = np.quantile(samples, 1 - alpha/2, axis=0)

        out = {}
        for i, c in enumerate(cols):
            out[c] = {
                "a": (float(lo[i]), float(hi[i])),
                "b": (float(lo[m+i]), float(hi[m+i])),
            }
        return out

    df = df_ancho
    cols = []
    for m in MODELS:
        cols.append(m[1])

    params, info = build_pairwise_ls(df, cols, ref_col=ref_LLM, ref_a=0.0, ref_b=1.0)

    print("INFO:", info)
    for c in cols:
        print(f"{c:25s}  a={params[c]['a']:+.6f}   b={params[c]['b']:+.6f}")

    ci_boot = bootstrap_confint(df, cols, ref_col=ref_LLM, B=2000, alpha=0.05)
    for c in df.columns:
        print(c,ci_boot[c])
