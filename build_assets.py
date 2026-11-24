import json, os, zipfile
from pathlib import Path

OUT = Path('/mnt/data/modulo1_fisica_interativo')
OUT.mkdir(parents=True, exist_ok=True)

# Helpers

def p(key, label, value, unit, minimum, maximum, step, hint=''):
    return {"key": key, "label": label, "value": value, "unit": unit, "min": minimum, "max": maximum, "step": step, "hint": hint}

def num_answer(formula, unit, tolerance=0.03, digits=2, display_scale=1, display_unit=None):
    return {"type": "numeric", "formula": formula, "unit": unit, "tolerance": tolerance, "digits": digits, "display_scale": display_scale, "display_unit": display_unit or unit}

def choice_answer(correct, explanation, options):
    return {"type": "choice", "correct": correct, "options": options, "explanation": explanation}

def ex(id, phase, n, title, topic, objective, context, scene, params, question, answer, hint, solution, visual_note=None, facts=None):
    return {
        "id": id, "phase": phase, "exercise_number": n, "title": title,
        "topic": topic, "estimated_minutes": 5 if answer["type"] == "numeric" else 4,
        "learning_objective": objective,
        "context": context,
        "simulation": {"scene": scene, "description": visual_note or context, "parameters": params,
                       "show_vectors": True, "show_live_readouts": True},
        "challenge": {"prompt": question, "answer": answer,
                      "hint": hint, "solution": solution},
        "completion": {"xp": 30 if phase in (1,2) else 35, "mastery_tag": topic}
    }

exercises = []

# PHASE 1 - CINEMÁTICA
exercises.append(ex(
    "fis1-cin-01", 1, 1, "Movimento retilíneo uniforme sem inclinação", "MRU",
    "Relacionar velocidade constante, tempo e deslocamento em uma trajetória retilínea.",
    "Um carrinho autônomo percorre uma pista reta com velocidade constante. O estudante altera a velocidade e o tempo e observa quanto o carrinho avança.",
    "mru_track", [p("v", "Velocidade", 6, "m/s", 0, 15, 0.5), p("t", "Tempo", 5, "s", 0, 10, 0.5), p("x0", "Posição inicial", 2, "m", 0, 20, 1)],
    "O carrinho parte da posição inicial indicada. Qual será sua posição depois do intervalo de tempo configurado? Considere a velocidade constante.",
    num_answer("mru_position", "m", 0.02, 1),
    "No MRU, a posição varia linearmente com o tempo: x = x₀ + v·t.",
    "Calcule primeiro o deslocamento Δx = v·t. Depois some esse deslocamento à posição inicial: x = x₀ + Δx.",
    "O carrinho se desloca pela pista; uma régua e marcadores indicam a posição inicial e a posição atual."
))
exercises.append(ex(
    "fis1-cin-02", 1, 2, "Movimento retilíneo uniforme em plano inclinado", "MRU no plano inclinado",
    "Distinguir o deslocamento ao longo da rampa de suas componentes horizontal e vertical.",
    "Um robô sobe uma rampa em velocidade constante. O estudante varia o ângulo da rampa, a velocidade e o tempo e observa a altura alcançada.",
    "incline_mru", [p("v", "Velocidade na rampa", 3, "m/s", 0.5, 8, 0.5), p("t", "Tempo", 4, "s", 0.5, 8, 0.5), p("theta", "Inclinação", 30, "°", 5, 60, 1)],
    "Qual é o ganho de altura vertical do robô durante o intervalo indicado? Considere movimento uniforme ao longo da rampa.",
    num_answer("incline_height_mru", "m", 0.03, 2),
    "Primeiro encontre o deslocamento sobre a rampa (v·t). A altura é a componente vertical desse deslocamento.",
    "Use Δs = v·t e, pelo triângulo retângulo, Δh = Δs·sen(θ).",
    "O robô sobe a rampa; um triângulo auxiliar destaca o deslocamento sobre a pista e a altura vertical."
))
exercises.append(ex(
    "fis1-cin-03", 1, 3, "Movimento retilíneo uniformemente variado sem inclinação", "MRUV",
    "Aplicar a equação horária do deslocamento em um movimento com aceleração constante.",
    "Um veículo de testes acelera em uma pista reta. O estudante modifica a velocidade inicial, a aceleração e o tempo e acompanha a separação entre os marcadores de posição.",
    "mruv_track", [p("v0", "Velocidade inicial", 2, "m/s", 0, 12, 0.5), p("a", "Aceleração", 1.5, "m/s²", 0, 4, 0.1), p("t", "Tempo", 4, "s", 0.5, 8, 0.5)],
    "Qual é o deslocamento do veículo durante o intervalo indicado? Considere aceleração constante e sentido positivo para a frente.",
    num_answer("mruv_displacement", "m", 0.03, 2),
    "A velocidade não permanece constante. Use Δx = v₀·t + (a·t²)/2.",
    "Substitua os valores na equação horária do deslocamento. A área sob o gráfico velocidade × tempo também representa o deslocamento.",
    "O veículo ganha velocidade ao longo da pista; os vetores de velocidade crescem durante a animação."
))
exercises.append(ex(
    "fis1-cin-04", 1, 4, "Movimento retilíneo uniformemente variado em queda livre", "Queda livre",
    "Relacionar altura, aceleração gravitacional e tempo de queda em uma situação sem resistência do ar.",
    "Uma esfera é solta do repouso de uma plataforma. O estudante altera a altura e o valor de g e observa a queda e o cronômetro.",
    "free_fall", [p("h", "Altura inicial", 45, "m", 5, 100, 1), p("g", "Gravidade", 10, "m/s²", 1, 15, 0.5)],
    "Desprezando a resistência do ar e considerando que a esfera é abandonada do repouso, quanto tempo ela leva para atingir o solo?", 
    num_answer("freefall_time", "s", 0.03, 2),
    "Como a velocidade inicial é zero, a distância de queda é h = (g·t²)/2.",
    "Isole o tempo: t = √(2h/g). A velocidade aumenta durante a queda, mas a aceleração permanece igual a g.",
    "A esfera cai verticalmente; o cronômetro e o vetor velocidade acompanham a evolução do movimento."
))
exercises.append(ex(
    "fis1-cin-05", 1, 5, "Movimento retilíneo uniformemente variado em plano inclinado", "MRUV no plano inclinado",
    "Identificar a componente do peso responsável pela aceleração ao longo de um plano inclinado ideal.",
    "Um bloco parte do repouso e desliza por uma rampa sem atrito. O estudante altera a inclinação e o tempo e observa a distância percorrida.",
    "incline_mruv", [p("theta", "Inclinação", 30, "°", 5, 60, 1), p("t", "Tempo", 2, "s", 0.5, 4, 0.25), p("g", "Gravidade", 10, "m/s²", 5, 15, 0.5)],
    "Desprezando o atrito, qual distância o bloco percorre ao longo da rampa no intervalo indicado? Ele parte do repouso.",
    num_answer("incline_mruv_distance", "m", 0.04, 2),
    "A aceleração ao longo do plano é a componente g·sen(θ). Como o bloco parte do repouso, Δs = a·t²/2.",
    "Calcule a = g·sen(θ) e depois Δs = (a·t²)/2. O ângulo usado é o da rampa em relação à horizontal.",
    "O bloco desliza pela rampa; uma seta paralela ao plano indica a componente da aceleração."
))
exercises.append(ex(
    "fis1-cin-06", 1, 6, "Movimento circular", "Movimento circular uniforme",
    "Relacionar raio e período à aceleração centrípeta de um movimento circular uniforme.",
    "Um carrinho percorre uma pista circular. O estudante altera o raio e o período de uma volta e observa a direção da velocidade e da aceleração centrípeta.",
    "circular", [p("r", "Raio da trajetória", 2, "m", 0.5, 5, 0.1), p("T", "Período", 4, "s", 1, 10, 0.25)],
    "Qual é o módulo da aceleração centrípeta do carrinho? Utilize π ≈ 3,1416.",
    num_answer("centripetal_acceleration", "m/s²", 0.04, 2),
    "No MCU, a velocidade escalar é constante, mas sua direção muda. Use aₙ = 4π²r/T².",
    "Calcule aₙ = 4π²r/T². A aceleração centrípeta aponta sempre para o centro da trajetória.",
    "O carrinho percorre uma circunferência; o vetor velocidade é tangente e o vetor aceleração aponta para o centro."
))

# PHASE 2 - DINÂMICA
exercises.append(ex(
    "fis1-din-01", 2, 1, "1ª Lei de Newton: princípio da inércia", "Inércia",
    "Explicar a tendência de um corpo de manter seu estado de repouso ou de movimento retilíneo uniforme quando a força resultante é nula.",
    "Um ônibus freia bruscamente e os passageiros parecem se projetar para a frente. O estudante observa a cena e identifica a explicação física.",
    "inertia_bus", [p("brake", "Intensidade da frenagem", 7, "nível", 1, 10, 1)],
    "Quando o ônibus freia, por que os passageiros tendem a se deslocar para a frente em relação ao veículo?",
    choice_answer(1, "Pela inércia: o corpo do passageiro tende a manter seu estado de movimento. O ônibus reduz sua velocidade, enquanto o corpo tende a continuar com a velocidade que possuía.", ["Porque o ônibus exerce uma força para a frente sobre os passageiros.", "Porque o corpo tende a manter seu estado de movimento enquanto o ônibus reduz a velocidade.", "Porque a gravidade aumenta durante a frenagem."]),
    "Pense no estado de movimento dos passageiros imediatamente antes de o ônibus frear.",
    "A 1ª Lei de Newton afirma que, se a força resultante sobre um corpo for nula, ele permanece em repouso ou em movimento retilíneo uniforme. A sensação de avanço não é uma força que empurra o passageiro para a frente.",
    "A animação mostra o ônibus desacelerando e o corpo do passageiro mantendo a tendência de movimento."
))
exercises.append(ex(
    "fis1-din-02", 2, 2, "1ª Lei de Newton: forças equilibradas", "Força resultante e inércia",
    "Calcular a força resultante em uma dimensão e relacioná-la à manutenção do estado de movimento.",
    "Duas equipes puxam um trenó em sentidos opostos. O estudante ajusta a intensidade de cada força e observa o equilíbrio ou o desequilíbrio.",
    "forces_balance", [p("right", "Força para a direita", 14, "N", 0, 30, 1), p("left", "Força para a esquerda", 14, "N", 0, 30, 1)],
    "Qual é o módulo e o sentido da força resultante sobre o trenó? Considere a direita como sentido positivo.",
    num_answer("net_force", "N", 0.02, 1),
    "Escolha um sentido positivo e faça a soma algébrica das forças: Fᵣ = Fdireita − Fesquerda.",
    "Subtraia a força para a esquerda da força para a direita. Se o resultado for zero, as forças estão equilibradas e a aceleração é nula.",
    "Duas setas opostas variam de tamanho conforme o estudante ajusta as forças; o vetor resultante é destacado."
))
exercises.append(ex(
    "fis1-din-03", 2, 3, "2ª Lei de Newton: força e aceleração", "Segunda Lei de Newton",
    "Calcular a aceleração resultante a partir da força resultante e da massa do corpo.",
    "Um carrinho de laboratório recebe uma força horizontal resultante. O estudante altera a massa e a força e observa como muda sua aceleração.",
    "newton_cart", [p("F", "Força resultante", 20, "N", 1, 50, 1), p("m", "Massa", 5, "kg", 1, 20, 0.5)],
    "Qual é a aceleração do carrinho para a força resultante e a massa indicadas?",
    num_answer("newton_acceleration", "m/s²", 0.03, 2),
    "A aceleração é diretamente proporcional à força resultante e inversamente proporcional à massa.",
    "Aplique a 2ª Lei de Newton: Fᵣ = m·a. Isole a aceleração: a = Fᵣ/m.",
    "O carrinho acelera na direção da força resultante; o vetor aceleração muda quando os controles são ajustados."
))
exercises.append(ex(
    "fis1-din-04", 2, 4, "2ª Lei de Newton: comparação de massas", "Massa e aceleração",
    "Comparar acelerações de corpos com massas diferentes submetidos à mesma força resultante.",
    "Dois carrinhos recebem forças horizontais de mesma intensidade, mas têm massas diferentes. O estudante compara a resposta de cada carrinho.",
    "compare_acceleration", [p("F", "Força em cada carrinho", 12, "N", 1, 30, 1), p("m1", "Massa do carrinho A", 3, "kg", 1, 12, 0.5), p("m2", "Massa do carrinho B", 6, "kg", 1, 18, 0.5)],
    "Qual é a diferença entre os módulos das acelerações dos dois carrinhos (aA − aB)?",
    num_answer("acceleration_difference", "m/s²", 0.04, 2),
    "Calcule a aceleração de cada carrinho separadamente usando a mesma força e massas diferentes.",
    "Use aA = F/mA e aB = F/mB. Depois calcule aA − aB. O carrinho de menor massa terá maior aceleração.",
    "Os dois carrinhos partem lado a lado; setas e medidores mostram acelerações diferentes."
))
exercises.append(ex(
    "fis1-din-05", 2, 5, "3ª Lei de Newton: ação e reação", "Terceira Lei de Newton",
    "Identificar pares de forças de ação e reação e reconhecer que atuam em corpos diferentes.",
    "Um foguete ejeta gases para trás e se desloca para a frente. O estudante observa o par de interações e identifica a lei envolvida.",
    "rocket_action", [p("thrust", "Intensidade da ejeção", 7, "nível", 1, 10, 1)],
    "Qual afirmação descreve corretamente o par de forças entre o foguete e os gases ejetados?",
    choice_answer(2, "O foguete exerce força sobre os gases e os gases exercem força de mesma intensidade e sentido oposto sobre o foguete. As forças atuam em corpos diferentes, por isso não se anulam entre si.", ["As duas forças atuam no foguete e se anulam.", "A força do foguete sobre os gases é maior.", "As forças têm mesma intensidade e sentidos opostos e atuam em corpos diferentes."]),
    "Observe que um dos corpos é o foguete e o outro é o conjunto de gases ejetados.",
    "Pela 3ª Lei de Newton, as forças de interação têm mesma intensidade, mesma direção e sentidos opostos, mas atuam em corpos diferentes.",
    "Os gases são lançados para trás e o foguete se desloca para a frente; os vetores de interação têm módulos iguais e sentidos opostos."
))
exercises.append(ex(
    "fis1-din-06", 2, 6, "3ª Lei de Newton: interação entre corpos", "Ação e reação e aceleração",
    "Aplicar a 3ª Lei de Newton e a 2ª Lei para determinar a aceleração de um dos corpos durante uma interação.",
    "Dois patinadores empurram um ao outro sobre uma superfície de baixo atrito. O estudante altera a massa de cada patinador e a intensidade da força de interação.",
    "skaters", [p("F", "Força de interação", 120, "N", 20, 240, 5), p("m1", "Massa do patinador A", 40, "kg", 20, 100, 5), p("m2", "Massa do patinador B", 60, "kg", 20, 120, 5)],
    "Qual é o módulo da aceleração do patinador A durante o empurrão?",
    num_answer("skater_a_acceleration", "m/s²", 0.04, 2),
    "A força sobre A tem o mesmo módulo da força sobre B. Use a massa de A para calcular sua aceleração.",
    "Pela 3ª Lei, o módulo da força sobre A é F. Pela 2ª Lei, aA = F/mA. As acelerações podem ser diferentes porque as massas são diferentes.",
    "Os patinadores se afastam em sentidos opostos; a força é igual em módulo e a aceleração depende da massa."
))

# PHASE 3 - TRABALHO, ENERGIA E POTÊNCIA
exercises.append(ex(
    "fis1-ene-01", 3, 1, "Conceito de trabalho e energia", "Trabalho mecânico",
    "Reconhecer que o trabalho de uma força está associado à transferência de energia e depende da componente da força na direção do deslocamento.",
    "Uma pessoa empurra uma parede que não se desloca e depois empurra uma caixa que desliza. O estudante compara as duas situações.",
    "work_wall_box", [p("push", "Força aplicada", 50, "N", 10, 100, 5)],
    "Em qual situação a força aplicada realiza trabalho mecânico sobre o objeto no modelo apresentado?",
    choice_answer(1, "Na caixa que se desloca. No modelo de trabalho mecânico, W = F·d·cos(θ). Se não há deslocamento do objeto, o trabalho dessa força é zero, mesmo que a pessoa faça esforço muscular.", ["Apenas na parede, pois há força aplicada.", "Na caixa que se desloca, pois há força e deslocamento.", "Nas duas situações, sempre que a pessoa faz esforço."]),
    "O trabalho mecânico depende do deslocamento do objeto, não apenas do esforço percebido pela pessoa.",
    "Na parede, o deslocamento é nulo, então W = 0. Na caixa, há deslocamento na direção da força, então a força realiza trabalho positivo.",
    "A simulação alterna a parede imóvel e a caixa em movimento, destacando o deslocamento."
))
exercises.append(ex(
    "fis1-ene-02", 3, 2, "Trabalho com força constante sem inclinação", "Trabalho de força constante",
    "Calcular o trabalho de uma força constante paralela ao deslocamento.",
    "Uma pessoa puxa uma caixa sobre um piso horizontal. O estudante altera a força aplicada e a distância percorrida.",
    "work_horizontal", [p("F", "Força aplicada", 50, "N", 5, 100, 5), p("d", "Deslocamento", 4, "m", 0.5, 10, 0.5), p("alpha", "Ângulo da força", 0, "°", 0, 90, 5)],
    "Qual é o trabalho realizado pela força aplicada durante o deslocamento? Considere o ângulo configurado entre força e deslocamento.",
    num_answer("work_constant", "J", 0.03, 2),
    "Use W = F·d·cos(α). Quando a força é paralela ao deslocamento, α = 0° e cos(0°) = 1.",
    "Multiplique a intensidade da força pelo deslocamento e pelo cosseno do ângulo entre os vetores.",
    "A caixa se desloca horizontalmente; a seta da força pode mudar de direção em relação ao deslocamento."
))
exercises.append(ex(
    "fis1-ene-03", 3, 3, "Trabalho com força constante em plano inclinado", "Trabalho em plano inclinado",
    "Calcular o trabalho de uma força aplicada ao longo do deslocamento em uma rampa e distinguir o ângulo da rampa do ângulo entre força e deslocamento.",
    "Uma equipe puxa um bloco para cima de uma rampa com força paralela à superfície. O estudante altera a força, o deslocamento e a inclinação da rampa.",
    "work_incline", [p("F", "Força aplicada", 35, "N", 5, 80, 5), p("d", "Deslocamento na rampa", 4, "m", 0.5, 8, 0.5), p("theta", "Inclinação da rampa", 25, "°", 5, 50, 1)],
    "Qual é o trabalho realizado pela força aplicada ao longo da rampa? Considere que a força é paralela ao deslocamento.",
    num_answer("work_incline", "J", 0.03, 2),
    "A inclinação da rampa não é o ângulo entre a força aplicada e o deslocamento: ambos apontam ao longo da rampa.",
    "Como a força é paralela ao deslocamento, α = 0° e W = F·d. A altura e a inclinação podem influenciar outras forças, mas não alteram o trabalho desta força aplicada para os mesmos F e d.",
    "O bloco sobe a rampa com uma força paralela à superfície; a componente vertical/horizontal fica indicada por um triângulo auxiliar."
))
exercises.append(ex(
    "fis1-ene-04", 3, 4, "Energia cinética", "Energia cinética",
    "Relacionar a energia cinética à massa e ao quadrado da velocidade.",
    "Um carrinho de laboratório percorre uma pista reta. O estudante altera a massa e a velocidade e observa a energia cinética calculada.",
    "kinetic_energy", [p("m", "Massa", 2, "kg", 0.5, 10, 0.5), p("v", "Velocidade", 6, "m/s", 0, 15, 0.5)],
    "Qual é a energia cinética do carrinho para os valores indicados?",
    num_answer("kinetic_energy", "J", 0.03, 2),
    "A energia cinética depende do quadrado da velocidade. Uma duplicação da velocidade quadruplica essa energia.",
    "Use Ec = (m·v²)/2. Substitua a massa em quilogramas e a velocidade em metros por segundo.",
    "O carrinho se move; um indicador de energia cresce com a massa e, principalmente, com o quadrado da velocidade."
))
exercises.append(ex(
    "fis1-ene-05", 3, 5, "Energia potencial gravitacional", "Energia potencial gravitacional",
    "Calcular a energia potencial gravitacional em relação a um nível de referência.",
    "Uma carga é elevada por um guindaste. O estudante altera a massa, a altura e a gravidade e observa o armazenamento de energia potencial.",
    "potential_gravity", [p("m", "Massa", 3, "kg", 0.5, 10, 0.5), p("h", "Altura", 5, "m", 0, 15, 0.5), p("g", "Gravidade", 10, "m/s²", 5, 15, 0.5)],
    "Qual é a energia potencial gravitacional da carga em relação ao nível de referência indicado?",
    num_answer("gravitational_potential", "J", 0.03, 2),
    "A energia potencial gravitacional aumenta com a massa, a gravidade e a altura em relação ao referencial.",
    "Use Epg = m·g·h. Considere o nível do chão como altura zero.",
    "O guindaste eleva a carga; uma régua vertical representa a altura e um medidor indica a energia potencial."
))
exercises.append(ex(
    "fis1-ene-06", 3, 6, "Energia potencial elástica", "Energia potencial elástica",
    "Calcular a energia armazenada em uma mola ideal deformada.",
    "Uma mola é comprimida por um bloco. O estudante altera a constante elástica e a deformação e observa a energia armazenada.",
    "spring", [p("k", "Constante elástica", 200, "N/m", 50, 500, 10), p("x", "Deformação", 0.3, "m", 0.05, 0.6, 0.01)],
    "Qual é a energia potencial elástica armazenada na mola para a deformação indicada?",
    num_answer("elastic_potential", "J", 0.04, 2),
    "A energia depende do quadrado da deformação: dobrar x quadruplica a energia armazenada.",
    "Use Epe = (k·x²)/2. A constante elástica deve estar em N/m e a deformação em metros.",
    "A mola se comprime e se distende; o indicador de energia aumenta com a deformação."
))
exercises.append(ex(
    "fis1-ene-07", 3, 7, "Conservação de energia: descida sem atrito", "Conservação da energia mecânica",
    "Aplicar a conservação da energia mecânica na transformação de energia potencial gravitacional em energia cinética.",
    "Um carrinho parte do repouso do alto de uma pista sem atrito e desce até o ponto mais baixo. O estudante altera a altura inicial.",
    "energy_hill", [p("h", "Altura inicial", 5, "m", 1, 12, 0.5), p("g", "Gravidade", 10, "m/s²", 5, 15, 0.5), p("m", "Massa do carrinho", 2, "kg", 0.5, 8, 0.5)],
    "Desprezando o atrito, qual é a velocidade do carrinho ao chegar ao nível mais baixo? Ele parte do repouso.",
    num_answer("energy_bottom_speed", "m/s", 0.04, 2),
    "No alto, a energia é potencial gravitacional; no ponto mais baixo, ela se transforma em energia cinética.",
    "Iguale m·g·h a m·v²/2. A massa aparece nos dois lados e pode ser simplificada: v = √(2gh).",
    "O carrinho desce uma pista curva; barras mostram a energia potencial diminuindo e a cinética aumentando."
))
exercises.append(ex(
    "fis1-ene-08", 3, 8, "Conservação de energia: dois níveis", "Conservação da energia mecânica",
    "Aplicar a conservação da energia mecânica quando o corpo inicia o movimento com velocidade diferente de zero e chega a uma altura intermediária.",
    "Um skatista passa por um ponto elevado com velocidade inicial e desce até uma plataforma mais baixa. O estudante altera as alturas e a velocidade inicial.",
    "energy_two_heights", [p("hi", "Altura inicial", 8, "m", 4, 12, 0.5), p("hf", "Altura final", 3, "m", 0, 10, 0.5), p("vi", "Velocidade inicial", 2, "m/s", 0, 8, 0.5), p("g", "Gravidade", 10, "m/s²", 5, 15, 0.5)],
    "Sem atrito, qual é a velocidade do skatista na altura final indicada? Considere hi maior que hf.",
    num_answer("energy_two_heights_speed", "m/s", 0.04, 2),
    "A energia cinética inicial também deve entrar na conservação: Ecᵢ + Epgᵢ = Ec𝒇 + Epg𝒇.",
    "Isole a velocidade final: vf = √(vi² + 2g(hi − hf)). A massa é simplificada na equação.",
    "O skatista passa por dois níveis; as barras de energia mostram a energia cinética inicial somada à conversão da energia potencial."
))

# PHASE 4 - GRAVITAÇÃO UNIVERSAL
exercises.append(ex(
    "fis1-gra-01", 4, 1, "Lei da Gravitação Universal", "Gravitação universal",
    "Compreender como a força gravitacional depende das massas e da distância entre os centros dos corpos.",
    "Dois corpos celestes interagem gravitacionalmente. O estudante altera a massa de um deles e a distância entre os corpos.",
    "gravity_field", [p("mratio", "Massa do corpo menor", 5, "nível", 1, 10, 1), p("distance", "Distância relativa", 5, "nível", 2, 10, 1)],
    "Qual alternativa descreve corretamente a dependência da força gravitacional entre dois corpos?",
    choice_answer(2, "A força é diretamente proporcional ao produto das massas e inversamente proporcional ao quadrado da distância entre seus centros: F = G·m₁·m₂/r².", ["Diretamente proporcional à distância.", "Proporcional ao produto das massas e inversamente proporcional ao quadrado da distância.", "Independe da distância entre os corpos."]),
    "Observe separadamente o efeito de aumentar uma das massas e o efeito de aumentar a distância.",
    "A Lei da Gravitação Universal é F = G·m₁·m₂/r². Se a distância dobra, mantendo as massas, a força passa a ser um quarto do valor inicial.",
    "Dois corpos são representados com linhas de campo esquemáticas e vetores de atração apontando um para o outro."
))
exercises.append(ex(
    "fis1-gra-02", 4, 2, "1ª Lei de Kepler: lei das órbitas", "Primeira Lei de Kepler",
    "Reconhecer que os planetas descrevem órbitas elípticas com o Sol localizado em um dos focos.",
    "O estudante observa uma órbita elíptica e compara a posição do Sol com o centro geométrico da elipse.",
    "kepler_ellipse", [p("ecc", "Excentricidade visual", 0.35, "", 0, 0.7, 0.05)],
    "De acordo com a 1ª Lei de Kepler, onde o Sol se localiza em relação à órbita elíptica de um planeta?",
    choice_answer(1, "O Sol fica em um dos focos da elipse, e não necessariamente no centro geométrico da órbita.", ["No centro geométrico da elipse.", "Em um dos focos da elipse.", "Fora do plano da órbita."]),
    "Observe que a elipse tem dois focos. O Sol não precisa estar no centro da figura.",
    "A 1ª Lei de Kepler afirma que os planetas descrevem órbitas elípticas, com o Sol em um dos focos.",
    "A órbita elíptica aparece com os dois focos destacados e o Sol em um deles."
))
exercises.append(ex(
    "fis1-gra-03", 4, 3, "2ª Lei de Kepler: lei das áreas", "Segunda Lei de Kepler",
    "Interpretar a lei das áreas e relacionar a velocidade orbital à distância do planeta ao Sol.",
    "Um planeta percorre uma órbita elíptica. O estudante observa setores varridos em intervalos de tempo iguais, próximos e distantes do Sol.",
    "kepler_area", [p("ecc", "Excentricidade visual", 0.45, "", 0.1, 0.7, 0.05)],
    "Em intervalos de tempo iguais, como se comparam as áreas varridas pelo segmento que liga o planeta ao Sol?",
    choice_answer(0, "As áreas são iguais. Por isso, o planeta se desloca mais rapidamente quando está próximo do Sol e mais lentamente quando está distante.", ["As áreas varridas são iguais em tempos iguais.", "O planeta percorre distâncias iguais em tempos iguais.", "O planeta tem velocidade constante em toda a órbita."]),
    "Compare os setores desenhados para o mesmo intervalo de tempo, um próximo e outro distante do Sol.",
    "A 2ª Lei de Kepler afirma que o raio vetor varre áreas iguais em tempos iguais. A velocidade orbital é maior no periélio e menor no afélio.",
    "Um setor próximo ao Sol e outro distante são destacados em intervalos de tempo equivalentes."
))
exercises.append(ex(
    "fis1-gra-04", 4, 4, "3ª Lei de Kepler: lei dos períodos", "Terceira Lei de Kepler",
    "Relacionar o período orbital ao tamanho da órbita e comparar corpos que orbitam o mesmo astro.",
    "Dois planetas orbitam a mesma estrela em órbitas de tamanhos diferentes. O estudante altera os semieixos maiores e compara os períodos.",
    "kepler_periods", [p("a1", "Semieixo maior A", 1, "UA (rel.)", 0.5, 2, 0.1), p("a2", "Semieixo maior B", 2, "UA (rel.)", 0.5, 3, 0.1)],
    "Qual planeta apresenta maior período orbital: o de menor ou o de maior semieixo maior?",
    choice_answer(1, "O planeta de maior semieixo maior possui maior período orbital. Para corpos que orbitam a mesma estrela, T² é proporcional a a³.", ["O de menor semieixo maior.", "O de maior semieixo maior.", "Os períodos são sempre iguais."]),
    "Aumentar o tamanho da órbita significa percorrer uma trajetória maior e, pela 3ª Lei, também aumenta o período.",
    "A 3ª Lei de Kepler estabelece T²/a³ = constante para corpos que orbitam o mesmo astro central.",
    "Duas órbitas com raios diferentes são animadas; o planeta externo demora mais para completar uma volta."
))
exercises.append(ex(
    "fis1-gra-05", 4, 5, "Lei da Gravitação Universal: cálculo da força", "Força gravitacional",
    "Calcular a intensidade da força gravitacional entre a Terra e um satélite em uma órbita circular aproximada.",
    "Um satélite de comunicação orbita a Terra. O estudante altera sua massa e a distância entre o satélite e o centro da Terra.",
    "satellite_orbit", [p("m", "Massa do satélite", 1000, "kg", 200, 3000, 100), p("r", "Raio orbital", 7000000, "m", 6600000, 15000000, 100000)],
    "Calcule o módulo da força gravitacional entre a Terra e o satélite. Use Mterra = 5,97×10²⁴ kg e G = 6,67×10⁻¹¹ N·m²/kg². Responda em kN.",
    num_answer("gravity_force_kn", "kN", 0.05, 2),
    "A distância r é medida do centro da Terra ao satélite, e não da superfície até o satélite.",
    "Use F = G·Mterra·msat/r². O resultado em newtons deve ser dividido por 1000 para obter quilonewtons.",
    "A Terra e o satélite são representados em escala esquemática; uma linha indica o raio orbital e outra a força de atração."
))
exercises.append(ex(
    "fis1-gra-06", 4, 6, "Velocidade de um satélite", "Velocidade orbital",
    "Relacionar velocidade orbital, massa do astro central e raio da órbita circular.",
    "Um satélite artificial percorre uma órbita circular ao redor da Terra. O estudante altera a altitude e observa a velocidade orbital necessária.",
    "satellite_orbit", [p("alt", "Altitude acima da superfície", 400000, "m", 200000, 2000000, 50000)],
    "Qual é aproximadamente a velocidade orbital do satélite a essa altitude? Use Mterra = 5,97×10²⁴ kg, Rterra = 6,37×10⁶ m e G = 6,67×10⁻¹¹. Responda em km/s.",
    num_answer("orbital_speed_kms", "km/s", 0.04, 2),
    "O raio da órbita é a soma do raio da Terra com a altitude. A massa do satélite não entra na expressão ideal.",
    "Para uma órbita circular, v = √(G·Mterra/r), com r = Rterra + altitude. Divida m/s por 1000 para obter km/s.",
    "O satélite percorre uma órbita circular; o vetor velocidade é tangente à trajetória."
))
exercises.append(ex(
    "fis1-gra-07", 4, 7, "Campo gravitacional", "Campo gravitacional",
    "Calcular a intensidade do campo gravitacional em uma distância definida do centro da Terra.",
    "Uma sonda mede o campo gravitacional em diferentes altitudes. O estudante altera a altitude e observa como o campo diminui com a distância.",
    "gravity_field", [p("alt", "Altitude", 400000, "m", 0, 3000000, 50000)],
    "Qual é a intensidade do campo gravitacional nessa altitude? Use Mterra = 5,97×10²⁴ kg, Rterra = 6,37×10⁶ m e G = 6,67×10⁻¹¹. Responda em m/s².",
    num_answer("field_strength", "m/s²", 0.04, 2),
    "A distância r deve ser medida a partir do centro da Terra: r = Rterra + altitude.",
    "Use g = G·Mterra/r². À medida que a distância ao centro aumenta, o campo gravitacional diminui.",
    "A sonda muda de altitude em relação à Terra; linhas esquemáticas representam o campo gravitacional."
))
exercises.append(ex(
    "fis1-gra-08", 4, 8, "Energia potencial gravitacional", "Energia potencial gravitacional gravitacional",
    "Interpretar o sinal e calcular a energia potencial gravitacional de um satélite em relação ao referencial no infinito.",
    "Um satélite está a uma distância r do centro da Terra. O estudante altera sua massa e o raio orbital e observa a energia potencial gravitacional.",
    "gravity_energy", [p("m", "Massa do satélite", 500, "kg", 100, 2000, 50), p("r", "Raio orbital", 7000000, "m", 6600000, 15000000, 100000)],
    "Considerando energia potencial gravitacional igual a zero no infinito, qual é a energia potencial do satélite? Responda em GJ (gigajoules), incluindo o sinal.",
    num_answer("gravity_potential_gj", "GJ", 0.05, 2),
    "Nesse referencial, a energia potencial gravitacional de um sistema ligado é negativa.",
    "Use U = −G·Mterra·msat/r. Converta joules para gigajoules dividindo por 10⁹.",
    "O satélite aparece em órbita e um indicador mostra a energia potencial negativa associada ao sistema Terra-satélite."
))

module = {
    "schema_version": "1.0.0",
    "language": "pt-BR",
    "subject": "Física",
    "module": 1,
    "title": "Movimento, forças, energia e gravitação",
    "source_alignment": {
        "document": "Roteiro módulos de ensino.pdf",
        "scope": "Física - 1º Módulo",
        "note": "Os nomes e a sequência das quatro fases e dos 28 exercícios seguem o roteiro enviado. Contextos, objetivos operacionais, valores numéricos, perguntas, gabaritos e propostas de simulação foram elaborados como sugestões didáticas para esta demonstração."
    },
    "constants": {"G": 6.67e-11, "earth_mass": 5.97e24, "earth_radius": 6.37e6, "pi": 3.141592653589793},
    "phases": [
        {"id": "fis1-fase-1", "number": 1, "title": "Cinemática", "description": "Descrever e analisar movimentos por meio de posição, velocidade, aceleração e tempo.", "exercise_ids": [e['id'] for e in exercises if e['phase']==1]},
        {"id": "fis1-fase-2", "number": 2, "title": "Dinâmica", "description": "Investigar as relações entre forças, massa e movimento por meio das Leis de Newton.", "exercise_ids": [e['id'] for e in exercises if e['phase']==2]},
        {"id": "fis1-fase-3", "number": 3, "title": "Trabalho, Energia e Potência", "description": "Relacionar forças, deslocamentos e transformações de energia.", "exercise_ids": [e['id'] for e in exercises if e['phase']==3]},
        {"id": "fis1-fase-4", "number": 4, "title": "Gravitação Universal", "description": "Compreender a interação gravitacional e as leis que descrevem órbitas.", "exercise_ids": [e['id'] for e in exercises if e['phase']==4]}
    ],
    "exercises": exercises
}

(OUT/'modulo1_fisica.json').write_text(json.dumps(module, ensure_ascii=False, indent=2), encoding='utf-8')
EXERCISE_DIR = OUT/'exercicios'
EXERCISE_DIR.mkdir(parents=True, exist_ok=True)
for exercise in exercises:
    (EXERCISE_DIR/f"{exercise['id']}.json").write_text(json.dumps(exercise, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Wrote {len(exercises)} exercises and individual JSON files")