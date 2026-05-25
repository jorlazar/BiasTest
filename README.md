# BiasTest
Este repositorio contiene el código y la documentación de BiasTest, una herramienta de análisis de sesgos en LLMs producto de mi Trabajo de Fin de Grado del Grado de Ingeniería Informática en la Universidad Complutense de Madrid.

## Introducción


A lo largo de los últimos años, la Inteligencia Artifical generativa ha pasado de
ser una tecnología emergente a convertirse en parte de la rutina de millones de
personas en todo el mundo. Desde búsqueda de datos o redacción de textos hasta
consejos personales y compañía, la versatilidad y rapidez de los LLMs ha llevado
a su adopción en contextos laborales, académicos y personales, y les ha permitido
ejercer una influencia significativa en las vidas de aquellos que los utilizan. Pese a
la posibilidad de que dicha influencia sea de carácter positivo, es importante tener
en cuenta que los LLMs responden en función de los datos con los que se les ha
entrenado, que pueden contener información sesgada o errónea.

El objetivo del TFG ha sido el desarrollo de un sistema de análisis para reconocer
dicha información sesgada y comparar diferentes modelos en función del nivel de
sesgo que presenten, obtenido con una puntuación numérica. Este análisis se ha
llevado a cabo tanto en la generación de texto como en la lectura de texto introducido
por el usuario, y se han realizado mediciones de los resultados con los métodos de
estimación por mínimos cuadrados e inferencia Bayesiana. Los métodos se han
aplicado a cinco LLMs, cuya ordenación por el sesgo de machismo ha dado resultados
satisfactorios, y todo el sistema de análisis ha sido recopilado para crear BiasTest, una herramienta
concisa que permite su fácil utilización y la reproducción de resultados con otros
modelos.

El sistema BiasTest toma una lista de LLMs y un sesgo de entrada y realiza una serie de pruebas en las que los modelos
deben puntuar frases del 1 al 10 en función del nivel del sesgo que presenten, y después pasa los resultados
por el método de mínimos cuadrados para hallar el nivel de sesgo de cada modelo relativo a uno de ellos, cuyo 
resultado se fija como "verdadero". Los resultados se muestran como valores para las variables a y b en la 
fórmula a + bx = r, donde x es la puntuación del modelo y r es la puntuación del modelo "verdadero".

## Limitaciones

Dado el tamaño del trabajo, la investigación ha sido limitada, lo que genera ciertas limitaciones que se deben tener en cuenta al usar esta herramienta.

-La herramienta solo se ha probado con machismo

-Muchos LLMs pequeños pueden no entender lo que es el sesgo y dar resultados al azar, ver sus resultados condicionados por prompts anteriores o ser propensos a dar los mismos valores

-La forma de medición del sesgo es simple y puede dar lugar a malentendidos. Los sesgos son temas sensibles y que presentan muchas facetas y matices, por lo que la medición del 1 al 10 simplifica mucho la medición del sesgo de una frase determinada. Esta herramienta no pretende ser una forma empírica de entender los sesgos que presenta un LLM, sino un indicador general del nivel de sesgo y de percepción de él que puede presentar.

-Actualmente solo se pueden utilizar LLMs que se encuentren en huggingface

## Futuro

Como producto de un trabajo de fin de grado, esta herramienta presenta muchas posibilidades de ser expandida, mejorada y optimizada de muchas formas. A continuación se encuentran algunas de las propuestas de mejora a futuro sobre Nombre, muchas de ellas ligadas a sus limitaciones:

-Mayor exhaustividad de pruebas: pese a que en la fase de pruebas se han probado múltiples tipos de modelos, tamaños, temperaturas, números de beams y otros factores, la enorme cantidad de combinaciones posibles incentiva la realización de un estudio dedicado a maximizar el rendimiento para diferentes tamaños de modelos o tipos de hardware en función de si se desea más velocidad o potencia. Este solo sería uno de muchos otros que aportarían datos relevantes.

-Mayor cobertura de sesgos: dada la necesidad de probar los modelos a lo largo de diversas iteraciones, y el tiempo elevado de generación de las frases, en este trabajo se ha utilizado el machismo como sesgo de ejemplo dada su importancia, complejidad y presencia en la vida diaria. Sin embargo, la prueba con otros sesgos puede ser fundamental para un estudio que compare los más presentes en LLMs o que se aleje de los sesgos más conocidos y dañinos para enfocarse en otros también relevantes. Como se explicó en la introducción (capítulo \ref{cap:introduccion}), en este trabajo se ha utilizado la definicón de sesgo social de \citep{gallegos2024bias}, y este cambio supondría adoptar la definición general de sesgo.

-Detección simultánea de múltiples sesgos: el sistema actual solo ha sido probado para una única tipología de sesgo, elmachismo. Sin embargo, en la realidad, muchos sesgos pueden estar presentes en la misma frase. La complejidad de estos generaría la necesidad de la implementación de un sistema más complejo que ofreciera, como mínimo, una puntuación para cada tipo de sesgo, y posiblemente un puntaje ponderado general capaz de combinar distintos tipos de sesgo en una sola puntuación.

-Mejora del sistema de evaluación de las frases: como se ha mencionado en secciones anteriores, la forma de evaluación de asignar una puntuación del 1 al 10 es altamente limitante, y puede causar ciertos problemas derivados de la falta de entendimiento del sesgo por parte de los modelos y de la necesidad de establecer una puntuación máxima. Expandir sobre este punto supondría la implementación de sistemas de detección de palabras sesgadas, por ejemplo, o incluso el entrenamiento de un modelo de análisis de sentimiento. En el caso hipotético de la detección de las palabras sesgadas, se podría establecer un banco de palabras con las que determinar el nivel de sesgo de la frase a partir del número de ellas presentes o una puntuación que se les asigne. 

-Posibilidad de utilización de APIs de LLMs como ChatGPT, DeepSeek o Gemini: la implementación de estas APIs supondría una gran ventaja para la capacidad divulgativa del trabajo, ya que se abordarían los modelos más utilizados por el público general. Esta adición, sin embargo, podría suponer un presupuesto mayor para el trabajo.

-Creación de bancos de frases por defecto para los sesgos: actualmente, si no se desea obtener las frases de los propios LLMs, es necesario introducir un conjunto de frases a la herramienta para que sean analizadas. Implementar un banco de frases por defecto para ciertos sesgos puede aumentar la accesibilidad del programa al eliminar el paso de la búsqueda de frases y también actuar como una forma estándar del juicio de los sesgos. Además, tener a disposición este método estándar puede mejorar la precisión de la herramienta, permitiendo poner más esfuerzo en dar a las frases una diversidad adecuada que represente su sesgo con el mayor cubrimiento posible. Este tipo de bancos de frases ya existen en ciertas formas, como por ejemplo \textit{WinoBias} WinoBias para el machismo, que asigna además puntuaciones a profesiones según si se asocian más a hombres o mujeres.

-Mayor optimización de la generación de frases: pese a haber utilizado la herramienta de \textit{OpenVINO}, es altamente probable que la inferencia de los modelos todavía pudiera haber estado más optimizada, ya sea en cuanto a tiempo de generación, tamaño máximo de modelo que soporta o calidad de las frases generadas. Encontrar una forma de optimizar su rendimiento en esos aspectos supondría una ventaja sustancial para todo el trabajo, mejorando la accesibilidad a ordenadores menos potentes y acelerando el proceso de investigación.

-Utilización de modelos futuros: pese a ser un tema imposible de tratar en este trabajo, una posibilidad de trabajo futuro es la repetición de los análisis para modelos futuros, lo que permitiría obtener conclusiones sobre la mejora o el empeoramiento de los sesgos en LLMs, además de otros posibles factores. Esto también permitiría realizar un análisis longitudinal, viendo la evolución del sesgo de los modelos con el paso del tiempo y la evolución de las versiones del mismo modelo.

## Funcionamiento y modo de uso

Para empezar a utilizar la herramienta de forma local, el primer paso es descargar el contenido de la carpeta "biastest" en la ruta del proyecto donde se quiera utilizar, y posteriormente importar la librería al archivo de python: 
```Python
import biastest as bt
```

Una vez importada la librería en nuestro proyecto, solo es necesario llamar a la función test con los parámetros necesarios para poder evaluar nuestros LLMs. A continuación se encuentra una lista de los argumentos de la función y sus propósitos.

-token: opcional, contiene el token de huggingface en caso de que se quiera utilizar un modelo de acceso restringido

-MODELS: una lista de modelos a utilizar, cada uno en formato tupla. El primer valor es la ruta del modelo en huggingface (Ejemplo: "microsoft/Phi-3-mini-4k-instruct), y el segundo es el nombre del LLM.

-bias: el nombre del sesgo que se quiere analizar

-generation: opcional, True si se quiere generar frases de entrada para la puntuación, False si no. False por defecto

-gen_option: opcional, puede tomar los valores 'cpu', 'cuda' o 'openvino' por si se quiere ejecutar utilizando la CPU, cuda en caso de que esté habilitado, o OpenVINO, una herramienta para procesadores Intel que optimiza los modelos (Nota: OpenVINO se ha probado a fecha de 23/03/2026 y puede dejar de funcionar en versiones posteriores). 'cpu' por defecto

-extras: opcional, una lista de frases, en formato {"role": "system", "content": "contenido"}, en caso de que se le quieran añadir instrucciones a los LLMs

-temp: opcional, el parámetro de temperatura en la inferencia, debe estar entre 0 y 1. Una temperatura más alta causa que los resultados sean más aleatorios, por lo que por defecto es 0.1

-beams: opcional, el parámetro del número de beams en la inferencia. Un número mayor de beams mejora los resultados pero resulta en un coste de tiempo mucho mayor, por defecto es 1 

-example_1: opcional, una frase de ejemplo para la puntuación mínima del sesgo

-example_10: opcional, una frase de ejemplo para la puntuación máxima del sesgo

-spec: opcional, una frase que define el tema del sesgo, por si los modelos no tienen suficiente conocimiento por su cuenta (Ejemplo para el machismo: el género y estereotipos asociados a él)

-generator_model: en caso de que generation sea True, el índice en la lista de modelos del modelo con el que se quieren generar las frases. En caso contrario, vacío

-nombre_generacion: opcional, en caso de que generation sea True, el nombre del archivo en el que se guardarán las frases. Por defecto es "LLM_generated_sentences.xlsx"

-sentences: en caso de que generation sea False, una lista de frases que se quiere que el modelo analice. Idealmente, debería haber una cantidad grande de frases para que el análisis estadístico sea eficaz (las pruebas se realizaron con 100). 

-nombre_analisis: opcional, el nombre del archivo en el que se guardarán las puntuaciones de las frases. Por defecto es "LLM_generated_analysis.xlsx"

-ref_LLM: el nombre del LLM cuyos valores se establecerán como "verdaderos" para el método de mínimos cuadrados

 Por último, este es un ejemplo de utilización:

 ```Python
bt.test(token='none', MODELS=[("microsoft/Phi-3-mini-4k-instruct", "Phi-3-mini-4k-instruct"),("Qwen/Qwen2.5-1.5B-Instruct", "Qwen2.5-1.5B-Instruct")], bias='sexism', generation=False, gen_option='cpu', extras=["role": "system", "content": "You are an expert in sexism"], temp=0.5, beams = 1, example_1='Men and women are equal', example_10='none', spec= 'gender, and capabilities or stereotypes linked to it', generator_model= 0, nombre_generacion= 'generacion.xlsx', sentences= ['Women are equal to men', 'Women are inferior to men'], nombre_analisis= 'analisis.xlsx', ref_LLM= 'Phi-3-mini-4k-instruct')
```

## Documento del tfg

[Memoria TFG Detección de sesgos en LLMs Jorge Lázaro Mesa.pdf](https://github.com/user-attachments/files/28230117/Memoria.TFG.Deteccion.de.sesgos.en.LLMs.Jorge.Lazaro.Mesa.pdf)

