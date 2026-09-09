## Do código ao serviço 
## Mini Radar ENEM com Python e Docker 

## 1. O que foi necessário instalar e configurar para executar a aplicação sem Docker? 
    Foi necessário instalar todas as bibliotecas, possuir Python na máquina, padronizar as dependências para, só depois, poder rodar a aplicação. Sem a conteinerização, todo o versionamento das dependências deve ser feito individualmente para evitar erros de execução. 

## 2. O que o Docker passou a empacotar ou padronizar? 

	O docker empacota todo o ambiente de execução necessário para rodar a aplicação: a versão da linguagem e as bibliotecas utilizadas - com suas respectivas versões. Deste modo, a possibilidade de incompatibilidade de dependências na hora de rodar a aplicação é mitigada, pois todas as versões são travadas pelo Docker.

## 3. Se o container for executado em uma VM IaaS, quais responsabilidades ainda ficam com a equipe? 
	
	A utilização de uma VM ainda deixa pendente OS, Runtime, Middleware, dados e a camada de aplicação. O docker pode empacotar o runtime e a aplicação, mas ainda deverá ser administrado pela equipe. Logo, a equipe é responsável por estes 5 atributos do software.


## 4. O que um PaaS poderia assumir automaticamente? 
	
	Um PaaS assume todas as responsabilidades, com exceção de: aplicação (código) e dados (banco de dados), que ainda ficariam a cargo da equipe responsável.

## 5. Por que Docker não pode ser classificado, sozinho, como IaaS, PaaS ou SaaS? 

	Porque o Docker é uma ferramenta de conteinerização de serviços e dependências. O que classifica um sistema como IaaS, PaaS ou SaaS tem relação ao controle ou delegação de atributos do sistema. 
            O rótulo fala sobre contexto, não necessariamente ferramentas utilizadas.
            IaaS, PaaS e SaaS dizem respeito à divisão de responsabilidades. O que a equipe irá operar e o que será delegado. Docker é tecnologia, não divisão de atribuições claras.

## 6. Qual modelo de serviço oferece o melhor equilíbrio entre controle, simplicidade, escalabilidade e custo para hospedar a aplicação? 
	Ao pensar nestes critérios, o melhor modelo de serviço é o PaaS. Nele, temos controle das versões e do ambiente de execução, do conteúdo dos dados e da aplicação. Abrimos mão somente da infra própria.
    Pagamos pelo uso, escalamos conforme a necessidade e “fugimos” das dores de cabeça que a administração de uma VM trazem.
    Entretanto, caso fosse necessário kernel próprio, soberania do servidor dos dados e carga constante e previsível, o cenário já mudaria muito em favor da IaaS. Portanto, percebe-se que alguns detalhes podem alterar completamente o modelo de serviço ideal. 
