import os
import re
import sys
import subprocess
from tkinter import Tk, filedialog


TIPOS_BRANCH = {
    "1": ("feature", "feat"),
    "2": ("fix", "fix"),
    "3": ("hotfix", "fix"),
    "4": ("refactor", "refactor"),
    "5": ("docs", "docs"),
    "6": ("test", "test"),
    "7": ("chore", "chore"),
    "8": ("style", "style"),
    "9": ("perf", "perf"),
    "10": ("ci", "ci"),
    "11": ("build", "build"),
}


def selecionar_pasta():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    caminho = filedialog.askdirectory()

    if not caminho:
        print("❌ Nenhuma pasta selecionada.")
        sys.exit()

    return caminho


def input_obrigatorio(msg):
    while True:
        valor = input(msg).strip()
        if valor:
            return valor
        print("❌ Esse campo não pode ser vazio.")


def executar_comando(cmd, cwd, etapa, mostrar_saida=True):
    print(f"\n--- {etapa} ---")
    print("Comando:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if mostrar_saida and result.stdout.strip():
        print("STDOUT:")
        print(result.stdout.strip())

    if result.stderr.strip():
        print("STDERR:")
        print(result.stderr.strip())

    if result.returncode != 0:
        print(f"❌ Erro na etapa: {etapa}")
        return False, result

    print(f"✅ Etapa concluída: {etapa}")
    return True, result


def executar_comando_silencioso(cmd, cwd):
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )


def repo_tem_git(caminho):
    return os.path.isdir(os.path.join(caminho, ".git"))


def repo_tem_origin(caminho):
    result = executar_comando_silencioso(
        ["git", "remote", "get-url", "origin"],
        caminho
    )
    return result.returncode == 0


def obter_branch_atual(caminho):
    result = executar_comando_silencioso(
        ["git", "branch", "--show-current"],
        caminho
    )
    if result.returncode == 0:
        return result.stdout.strip() or "(sem branch)"
    return "(desconhecida)"


def repo_tem_alteracoes(caminho):
    result = executar_comando_silencioso(
        ["git", "status", "--porcelain"],
        caminho
    )
    return bool(result.stdout.strip())


def branch_existe_local(caminho, nome_branch):
    result = executar_comando_silencioso(
        ["git", "show-ref", "--verify", f"refs/heads/{nome_branch}"],
        caminho
    )
    return result.returncode == 0


def branch_existe_remoto(caminho, nome_branch):
    result = executar_comando_silencioso(
        ["git", "ls-remote", "--heads", "origin", nome_branch],
        caminho
    )
    return bool(result.stdout.strip())


def normalizar_nome(texto):
    texto = texto.strip().lower()
    texto = texto.replace("_", "-")
    texto = re.sub(r"\s+", "-", texto)
    texto = re.sub(r"[^a-z0-9\-\/]", "", texto)
    texto = re.sub(r"-+", "-", texto)
    texto = texto.strip("-/")
    return texto


def mostrar_resumo_repo(caminho):
    print("\n=== REPOSITÓRIO ATUAL ===")
    print("Pasta:", caminho)
    print("Tem .git:", "Sim" if repo_tem_git(caminho) else "Não")

    if repo_tem_git(caminho):
        print("Branch atual:", obter_branch_atual(caminho))
        print("Tem origin:", "Sim" if repo_tem_origin(caminho) else "Não")
        print("Tem alterações:", "Sim" if repo_tem_alteracoes(caminho) else "Não")


def configurar_git(caminho_projeto):
    if repo_tem_git(caminho_projeto):
        print("✅ Já existe .git nessa pasta.")
    else:
        ok, _ = executar_comando(["git", "init"], caminho_projeto, "Inicializar repositório")
        if not ok:
            return

    if repo_tem_origin(caminho_projeto):
        print("✅ Remote origin já está configurado.")
        link_repo = None
    else:
        link_repo = input_obrigatorio("Link do repositório: ")

    if not repo_tem_alteracoes(caminho_projeto):
        print("⚠️ Não há alterações para commit inicial.")
    else:
        commit = input_obrigatorio("Commit inicial: ")

        etapas = [
            (["git", "add", "."], "Adicionar arquivos"),
            (["git", "commit", "-m", f"chore: {commit}"], "Criar commit inicial"),
        ]

        for cmd, etapa in etapas:
            ok, _ = executar_comando(cmd, caminho_projeto, etapa)
            if not ok:
                return

    branch_atual = obter_branch_atual(caminho_projeto)
    if branch_atual != "main":
        ok, _ = executar_comando(
            ["git", "branch", "-M", "main"],
            caminho_projeto,
            "Renomear branch para main"
        )
        if not ok:
            return

    if link_repo:
        ok, _ = executar_comando(
            ["git", "remote", "add", "origin", link_repo],
            caminho_projeto,
            "Adicionar remote origin"
        )
        if not ok:
            return

    if repo_tem_origin(caminho_projeto):
        ok, _ = executar_comando(
            ["git", "push", "-u", "origin", "main"],
            caminho_projeto,
            "Enviar main para o remoto"
        )
        if not ok:
            print("⚠️ Não foi possível fazer push da main.")
            return

    print("\n🎉 Configuração do Git concluída com sucesso.")


def atualizar_main(caminho_projeto):
    if not repo_tem_git(caminho_projeto):
        print("❌ Essa pasta não é um repositório Git.")
        return False

    if not repo_tem_origin(caminho_projeto):
        print("❌ Esse repositório não possui remote origin configurado.")
        return False

    etapas = [
        (["git", "checkout", "main"], "Ir para main"),
        (["git", "pull", "origin", "main"], "Atualizar main"),
    ]

    for cmd, etapa in etapas:
        ok, _ = executar_comando(cmd, caminho_projeto, etapa)
        if not ok:
            return False

    return True


def escolher_tipo_branch():
    print("\n=== TIPOS DE BRANCH ===")
    for chave, (tipo_branch, tipo_commit) in TIPOS_BRANCH.items():
        print(f"{chave} - {tipo_branch} ({tipo_commit})")

    while True:
        op = input("Escolha o tipo: ").strip()
        if op in TIPOS_BRANCH:
            return TIPOS_BRANCH[op]
        print("❌ Tipo inválido.")


def criar_branch_commit_push(caminho_projeto):
    if not repo_tem_git(caminho_projeto):
        print("❌ Essa pasta não é um repositório Git.")
        return

    if not repo_tem_origin(caminho_projeto):
        print("❌ Esse repositório não possui remote origin configurado.")
        return

    if not atualizar_main(caminho_projeto):
        return

    tipo_branch, tipo_commit = escolher_tipo_branch()

    escopo = input_obrigatorio(f"Nome/escopo da branch {tipo_branch}: ")
    msg_commit = input_obrigatorio(f"Mensagem do commit {tipo_commit}: ")

    escopo_normalizado = normalizar_nome(escopo)
    nome_branch = f"{tipo_branch}/{escopo_normalizado}"

    if branch_existe_local(caminho_projeto, nome_branch):
        print(f"❌ A branch local '{nome_branch}' já existe.")
        return

    if branch_existe_remoto(caminho_projeto, nome_branch):
        print(f"❌ A branch remota '{nome_branch}' já existe.")
        return

    etapas = [
        (["git", "checkout", "-b", nome_branch], f"Criar branch {nome_branch}"),
    ]

    for cmd, etapa in etapas:
        ok, _ = executar_comando(cmd, caminho_projeto, etapa)
        if not ok:
            return

    if not repo_tem_alteracoes(caminho_projeto):
        print("⚠️ Nenhuma alteração encontrada para commit.")
        print("✅ Branch criada com sucesso, mas sem commit.")
        return

    etapas = [
        (["git", "add", "."], "Adicionar alterações"),
        (["git", "commit", "-m", f"{tipo_commit}: {msg_commit}"], "Criar commit"),
        (["git", "push", "-u", "origin", nome_branch], f"Enviar branch {nome_branch}"),
    ]

    for cmd, etapa in etapas:
        ok, _ = executar_comando(cmd, caminho_projeto, etapa)
        if not ok:
            print(f"\n⚠️ Fluxo interrompido na etapa: {etapa}")
            return

    print(f"\n🎉 Fluxo da branch '{nome_branch}' concluído com sucesso.")
    print("💡 Próximo passo: abrir um PR para a main.")


def commitar_branch_atual(caminho_projeto):
    if not repo_tem_git(caminho_projeto):
        print("❌ Essa pasta não é um repositório Git.")
        return

    if not repo_tem_origin(caminho_projeto):
        print("❌ Esse repositório não possui remote origin configurado.")
        return

    branch_atual = obter_branch_atual(caminho_projeto)
    if branch_atual in ("main", "(sem branch)", "(desconhecida)"):
        print(f"❌ Você está na branch '{branch_atual}'.")
        print("⚠️ Evite commitar direto na main por esse fluxo.")
        return

    if not repo_tem_alteracoes(caminho_projeto):
        print("⚠️ Nenhuma alteração encontrada para commit.")
        return

    print(f"✅ Branch atual: {branch_atual}")
    tipo_commit = input_obrigatorio("Tipo do commit (feat, fix, docs, refactor, chore...): ")
    msg_commit = input_obrigatorio("Mensagem do commit: ")

    etapas = [
        (["git", "add", "."], "Adicionar alterações"),
        (["git", "commit", "-m", f"{tipo_commit}: {msg_commit}"], "Criar commit"),
        (["git", "push"], "Enviar alterações"),
    ]

    for cmd, etapa in etapas:
        ok, _ = executar_comando(cmd, caminho_projeto, etapa)
        if not ok:
            print(f"\n⚠️ Fluxo interrompido na etapa: {etapa}")
            return

    print("\n🎉 Commit e push realizados com sucesso na branch atual.")


def ver_status_git(caminho_projeto):
    if not repo_tem_git(caminho_projeto):
        print("❌ Essa pasta não é um repositório Git.")
        return

    executar_comando(["git", "status"], caminho_projeto, "Status do repositório")


def ver_log_resumido(caminho_projeto):
    if not repo_tem_git(caminho_projeto):
        print("❌ Essa pasta não é um repositório Git.")
        return

    executar_comando(
        ["git", "log", "--oneline", "--graph", "--decorate", "-10"],
        caminho_projeto,
        "Últimos commits"
    )


def menu():
    caminho_projeto = selecionar_pasta()

    while True:
        mostrar_resumo_repo(caminho_projeto)

        print("\n=== MENU ===")
        print("1 - Configurar Git")
        print("2 - Criar branch + commit + push")
        print("3 - Commitar e dar push na branch atual")
        print("4 - Atualizar main")
        print("5 - Ver status")
        print("6 - Ver log resumido")
        print("7 - Escolher outra pasta")
        print("8 - Sair")

        op = input("Escolha uma opção: ").strip()

        if op == "1":
            configurar_git(caminho_projeto)

        elif op == "2":
            criar_branch_commit_push(caminho_projeto)

        elif op == "3":
            commitar_branch_atual(caminho_projeto)

        elif op == "4":
            atualizar_main(caminho_projeto)

        elif op == "5":
            ver_status_git(caminho_projeto)

        elif op == "6":
            ver_log_resumido(caminho_projeto)

        elif op == "7":
            caminho_projeto = selecionar_pasta()
            print("✅ Nova pasta selecionada:", caminho_projeto)

        elif op == "8":
            print("Saindo...")
            break

        else:
            print("❌ Opção inválida.")


if __name__ == "__main__":
    menu()