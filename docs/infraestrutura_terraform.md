# ☁️ Infraestrutura como Código (IaC) com Terraform

Este documento detalha a estratégia de infraestrutura utilizada no projeto **ChurnInsight**, implementada na **Oracle Cloud Infrastructure (OCI)** utilizando **Terraform**.

## 🧐 O que é Terraform?

O Terraform é uma ferramenta de **Infraestrutura como Código (IaC)**. Em vez de criar servidores, redes e regras de firewall clicando manualmente em botões no console da nuvem (o que é propenso a erros e difícil de replicar), nós **escrevemos a infraestrutura em código**.

Isso nos permite:
1.  **Versionar** a infraestrutura (assim como fazemos com o código Java/Python).
2.  **Replicar** o ambiente inteiro em minutos em caso de falhas (Disaster Recovery).
3.  **Auditar** as configurações de segurança.

---

## 🏗️ Arquitetura Implementada no Projeto

O script Terraform deste projeto (`infra_oci/`) é responsável por provisionar automaticamente todo o ambiente necessário para rodar nossos containers Docker.

### Recursos Criados na Oracle Cloud:

1.  **Rede Virtual (VCN & Subnets):**
    *   Criação de uma *Virtual Cloud Network* isolada.
    *   Configuração de *Internet Gateway* e *Route Tables* para permitir acesso externo.

2.  **Segurança (Hardening):**
    *   Implementação de *Security Lists* (Firewall).
    *   **Regra de Entrada:** Apenas as portas **22** (SSH para manutenção) e **8501** (Frontend da Aplicação) estão abertas. Todo o resto é bloqueado por padrão.

3.  **Computação (Compute Instance):**
    *   Provisionamento de uma VM **Ubuntu 22.04**.
    *   Arquitetura **Ampere (ARM)** para alta performance e eficiência energética.

4.  **Automação (Cloud-Init):**
    *   O Terraform injeta um script de inicialização que:
        *   Instala o Docker e Docker Compose.
        *   Clona este repositório do GitHub.
        *   Configura as variáveis de ambiente (segredos) de forma segura.
        *   Executa o deploy da aplicação (`docker compose up`).

---

## 🔒 Segurança e Segredos

Por motivos de segurança, **nenhuma chave de API ou credencial é armazenada neste repositório**.

*   O Terraform utiliza **injeção de variáveis** em tempo de execução.
*   As chaves privadas (SSH e OCI API Key) são mantidas apenas no ambiente local do desenvolvedor responsável pelo deploy ou na pipeline de CI/CD, nunca no código-fonte.

---

## 🚀 Como Executar (Para Desenvolvedores)

Se você possui as credenciais de acesso ao tenancy da Oracle, siga os passos:

1.  Acesse a pasta de infraestrutura:
    ```bash
    cd infra_oci
    ```
2.  Inicialize o Terraform:
    ```bash
    terraform init
    ```
3.  Visualize o plano de execução:
    ```bash
    terraform plan
    ```
4.  Aplique a infraestrutura:
    ```bash
    terraform apply
    ```
    *(Após a confirmação, o IP de acesso da aplicação será exibido no terminal).*

5.  Para destruir o ambiente (economizar recursos):
    ```bash
    terraform destroy
    ```