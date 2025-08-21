from agents.router import create_agent, list_agents, run_agent
from services.audio import audio_to_text

if __name__ == "__main__":
    print("🤖 Jarvis BOT listo.")

    while True:
        cmd = input("\n> ").strip().lower()

        if cmd == "crear":
            name = input("Nombre del agente: ")
            desc = input("Descripción: ")
            agent = create_agent(name, desc, agent_type="memory")
            print(f"Agente creado: {agent.name}")

        elif cmd == "listar":
            agents = list_agents()
            for k, v in agents.items():
                print(f"[{k}] {v['name']} - {v['description']}")

        elif cmd == "run":
            agent_id = input("ID del agente: ")
            task = input("Tarea: ")
            print(run_agent(agent_id, task))

        elif cmd == "audio":
            path = input("Ruta del archivo de audio: ")
            print("Texto detectado:", audio_to_text(path))

        elif cmd == "salir":
            break

