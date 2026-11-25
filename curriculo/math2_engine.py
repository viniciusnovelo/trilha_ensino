"""Motor matemático seguro do Matemática 2. Fórmulas explícitas; sem eval."""
import math
FORMULAS={"euler_edges","prism_vertices","prism_volume","prism_total_area","cylinder_volume","cone_volume","sphere_area","sine_angle","sine_period","cosine_max","tangent_period","sine_rule_side","cosine_rule_side","matrix_add_11","matrix_product_11","determinant_2","determinant_3","system_x","system_y","cramer_x","counting_product","factorial","permutation","arrangement","combination","simple_probability","independent_union","exponential_value","population_growth","compound_amount_2","half_life_amount","logarithm_inverse"}
def calculate(formula,p):
    if formula not in FORMULAS: raise ValueError(f"Fórmula não suportada: {formula}")
    def v(k):
        x=float(p[k])
        if not math.isfinite(x): raise ValueError(f"Parâmetro inválido: {k}")
        return x
    def fact(n):
        n=int(n)
        if n<0 or n>170: raise ValueError("Fatorial fora do limite seguro.")
        return math.factorial(n)
    if formula=="euler_edges": r=v("vertices")+v("faces")-2
    elif formula=="prism_vertices": r=2*v("sides")
    elif formula=="prism_volume": r=v("base_area")*v("height")
    elif formula=="prism_total_area": r=v("base_perimeter")*v("height")+2*v("base_area")
    elif formula=="cylinder_volume": r=math.pi*v("radius")**2*v("height")
    elif formula=="cone_volume": r=math.pi*v("radius")**2*v("height")/3
    elif formula=="sphere_area": r=4*math.pi*v("radius")**2
    elif formula=="sine_angle": r=math.sin(math.radians(v("angle")))
    elif formula=="sine_period": r=2*math.pi/abs(v("frequency"))
    elif formula=="cosine_max": r=abs(v("amplitude"))+v("shift")
    elif formula=="tangent_period": r=math.pi/abs(v("frequency"))
    elif formula=="sine_rule_side": r=v("side_a")*math.sin(math.radians(v("angle_b")))/math.sin(math.radians(v("angle_a")))
    elif formula=="cosine_rule_side": r=math.sqrt(v("side_a")**2+v("side_b")**2-2*v("side_a")*v("side_b")*math.cos(math.radians(v("angle_c"))))
    elif formula=="matrix_add_11": r=v("a")+v("d")
    elif formula=="matrix_product_11": r=v("k")+4
    elif formula=="determinant_2": r=v("a")*v("d")-v("b")*v("c")
    elif formula=="determinant_3":
        a,b,c,d,e,f,g,h,i=[v(k) for k in "abcdefghi"]; r=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    elif formula in ("system_x","system_y","cramer_x"):
        a,b,c,d,e,f=[v(k) for k in "abcdef"]; det=a*e-b*d
        if abs(det)<1e-12: raise ValueError("Sistema sem solução única.")
        r=(c*e-b*f)/det if formula in ("system_x","cramer_x") else (a*f-c*d)/det
    elif formula=="counting_product": r=v("shirts")*v("pants")*v("hats")
    elif formula in ("factorial","permutation"): r=fact(v("n"))
    elif formula=="arrangement":
        n,k=int(v("n")),int(v("k"))
        if not 0<=k<=n: raise ValueError("É necessário 0 ≤ k ≤ n.")
        r=fact(n)/fact(n-k)
    elif formula=="combination":
        n,k=int(v("n")),int(v("k"))
        if not 0<=k<=n: raise ValueError("É necessário 0 ≤ k ≤ n.")
        r=fact(n)/(fact(k)*fact(n-k))
    elif formula=="simple_probability":
        if v("total")<=0: raise ValueError("Total deve ser positivo.")
        r=100*v("favorable")/v("total")
    elif formula=="independent_union":
        a,b=v("pA")/100,v("pB")/100; r=100*(a+b-a*b)
    elif formula=="exponential_value": r=v("a")*v("base")**v("x")
    elif formula=="population_growth": r=v("initial")*(1+v("rate")/100)**v("periods")
    elif formula=="compound_amount_2": r=v("capital")*(1+v("rate")/100)**v("periods")
    elif formula=="half_life_amount":
        if v("half")<=0: raise ValueError("Meia-vida deve ser positiva.")
        r=v("initial")*0.5**(v("time")/v("half"))
    elif formula=="logarithm_inverse": r=v("base")**v("exponent")
    else: raise ValueError("Fórmula não implementada.")
    if not math.isfinite(r): raise ValueError("Resultado inválido.")
    return r
def is_correct(submitted,expected,tolerance):
    a,b,t=map(float,(submitted,expected,tolerance))
    return all(map(math.isfinite,(a,b,t))) and t>=0 and abs(a-b)<=t
