def truncar_float(numero, casas_decimais=2):
    fator = 10 ** casas_decimais
    return int(numero * fator) / fator