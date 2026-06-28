import secrets
import string
""" Secrets: Es un generador pseudoaleatorio, similar a random pero mucho más seguro, 
ya que este le pide aleatoriedad directamente al SO, el SO le entrega una "mezcla"
de una recolección del caos impredecible de la computadora (los milisegundos entre que 
presionas una tecla, movimientos del mouse, variaciones térmicas del procesador, 
latencia del disco duro, etc) siendo criptográficamente seguro, y 
es ideal para la generación de contraseñas """

def generar_password_clasica(longitud=16):
    # Definimos el "alfabeto" (letras mayúsculas, minúsculas, números y símbolos seguros)
    simbolos_seguros = "-_@.!#*?"
    alfabeto = string.ascii_letters + string.digits + simbolos_seguros
    # alfabeto : abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_@.!#*?
   
    # Elegimos caracteres al azar de forma criptográficamente segura
    password = ''.join(secrets.choice(alfabeto) for i in range(longitud))
    
    return password



def main():
    numClaves = input("Ingrese la cantidad de claves a generar: ")
    largo = input("Ingrese la longitud de las claves a generar (entre 64 a 128 caracteres): ")
    for i in range(int(numClaves)):
        print(generar_password_clasica(int(largo)) + "\n") 
        # Ejemplo de salida:  qT!8x#mP2$kL9v@z


if __name__ == '__main__':
    main()