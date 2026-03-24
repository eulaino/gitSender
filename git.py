import os
import subprocess
from tkinter import Tk, filedialog


def selecionar_pasta():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    caminho = filedialog.askdirectory()

    if not caminho:
        print("Nenhuma pasta selecionada.")
        exit()

    return caminho


def executar_comando(cmd, cwd, etapa):
    print(f"\n--- {etapa} ---")
    print("Comando:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print("STDOUT:")
        print(result.stdout.strip())

    if result.stderr.strip():
        print("STDERR:")
        print(result.stderr.strip())

    if result.returncode != 0:
        print(f"❌ Erro na etapa: {etapa}")
        return False

    print(f"✅ Etapa concluída: {etapa}")
    return True


def repo_tem_git(caminho):
    return os.path.isdir(os.path.join(caminho, ".git"))


def repo_tem_origin(caminho):
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=caminho,
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def configurar_git(caminho_projeto):
    if repo_tem_git(caminho_projeto):
        print("✅ Já existe .git nessa pasta.")
    else:
        if not executar_comando(["git", "init"], caminho_projeto, "Inicializar repositório"):
            return

    link_repo = input("Link do repositório: ").strip()
    commit = input("Commit inicial: ").strip()

    etapas = [
        (["git", "add", "."], "Adicionar arquivos"),
        (["git", "commit", "-m", f"chore: {commit}"], "Criar commit inicial"),
        (["git", "branch", "-M", "main"], "Renomear branch para main"),
    ]

    for cmd, etapa in etapas:
        if not executar_comando(cmd, caminho_projeto, etapa):
            return

    if repo_tem_origin(caminho_projeto):
        print("✅ Remote origin já está configurado.")
    else:
        if not executar_comando(
            ["git", "remote", "add", "origin", link_repo],
            caminho_projeto,
            "Adicionar remote origin"
        ):
            return

    if not executar_comando(
        ["git", "push", "-u", "origin", "main"],
        caminho_projeto,
        "Enviar main para o remoto"
    ):
        return

    print("\n🎉 Configuração do Git concluída com sucesso.")


def fluxo_branch(caminho_projeto, tipo_branch, tipo_commit):
    if not repo_tem_git(caminho_projeto):
        print("❌ Essa pasta não é um repositório Git.")
        return

    if not repo_tem_origin(caminho_projeto):
        print("❌ Esse repositório não possui remote origin configurado.")
        return

    nome_espaco = input(f"Espaço da {tipo_branch}: ").strip()
    msg_commit = input(f"Mensagem de {tipo_branch}: ").strip()

    nome_branch = f"{tipo_branch}/{nome_espaco}"

    etapas = [
        (["git", "checkout", "-b", nome_branch], f"Criar branch {nome_branch}"),
        (["git", "add", "."], "Adicionar alterações"),
        (["git", "commit", "-m", f"{tipo_commit}: {msg_commit}"], "Criar commit"),
        (["git", "push", "-u", "origin", nome_branch], f"Enviar branch {nome_branch}"),
        (["git", "checkout", "main"], "Voltar para main"),
        (["git", "merge", nome_branch], f"Fazer merge da {nome_branch} na main"),
        (["git", "push"], "Enviar main atualizada"),
    ]

    for cmd, etapa in etapas:
        if not executar_comando(cmd, caminho_projeto, etapa):
            print(f"\n⚠️ Fluxo interrompido na etapa: {etapa}")
            return

    print(f"\n🎉 Fluxo de {tipo_branch} concluído com sucesso.")


def menu():
    caminho_projeto = selecionar_pasta()

    while True:
        print("\n=== MENU ===")
        print("1 - Configurar git")
        print("2 - Feature")
        print("3 - Fix")
        print("4 - Escolher outra pasta")
        print("5 - Sair")

        try:
            op = int(input("Escolha uma opção: ").strip())
        except ValueError:
            print("❌ Digite um número válido.")
            continue

        if op == 1:
            configurar_git(caminho_projeto)

        elif op == 2:
            fluxo_branch(caminho_projeto, "feature", "feat")

        elif op == 3:
            fluxo_branch(caminho_projeto, "fix", "fix")

        elif op == 4:
            caminho_projeto = selecionar_pasta()
            print("✅ Nova pasta selecionada:", caminho_projeto)

        elif op == 5:
            print("Saindo...")
            break

        else:
            print("❌ Opção inválida.")


menu()