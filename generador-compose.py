import sys

def generar_yaml_compose(nombre_archivo, cantidad_clientes):
    contenido = """name: tp0
services:
  server:
    container_name: server
    image: server:latest
    volumes:
      - ./server/config.ini:/config.ini:ro
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
      
"""

    for i in range(1, cantidad_clientes + 1):
        contenido += f"""  client{i}:
    container_name: client{i}
    image: client:latest
    volumes:
      - ./client/config.yaml:/config.yaml:ro
      - ./.data/agency-{i}.csv:/.data/agency.csv:ro
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - NOMBRE=Santiago
      - APELLIDO=Lorca
      - DOCUMENTO=30904465
      - NACIMIENTO=1999-03-17
      - NUMERO=7574
    networks:
      - testing_net
    depends_on:
      - server
"""

    contenido += """
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

    with open(nombre_archivo, 'w') as archivo:
        archivo.write(contenido)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Se necesitan recibir dos parametros: ./generar-compose.sh <archivo_salida> <cantidad_clientes>")
        sys.exit(1)

    archivo_salida = sys.argv[1]
    try:
        cantidad_clientes = int(sys.argv[2])
    except ValueError:
        print("El segundo parametro debe ser un numero entero.")
        sys.exit(1)

    generar_yaml_compose(archivo_salida, cantidad_clientes)
    