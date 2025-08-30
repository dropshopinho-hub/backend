# Tool Management System

Sistema de gestão de ferramentas desenvolvido com React (frontend) e Flask (backend).

## Última atualização
- Sistema de devolução com aprovação implementado
- Deploy automático configurado (Flask/Python) e o frontend (React/Vite) para o Sistema de Gestão de Ferramentas.

## Como compartilhar e instalar em outro computador

### 1. Pré-requisitos
- Python 3.11 ou superior
- Node.js (recomendado versão 18 ou superior)
- pnpm (gerenciador de pacotes Node.js)

### 2. Instalação

#### Backend
1. Navegue até a pasta `tool-management-backend`.
2. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
3. (Opcional) Para manter os dados, copie o arquivo `src/database/app.db` para o novo computador.
4. Inicie o backend:
   ```sh
   python src/main.py
   ```

#### Frontend
1. Navegue até a pasta `tool-management-frontend`.
2. Instale as dependências:
   ```sh
   pnpm install
   ```
3. Inicie o frontend:
   ```sh
   pnpm dev
   ```

### 3. Acesso
Abra o navegador e acesse:
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: conforme configurado (por padrão, http://localhost:5000)

### 4. Compartilhando usuários
- Para que outros usuários acessem, compartilhe o projeto e as instruções acima.
- Cada usuário pode acessar pelo navegador em sua máquina.
- Para uso em rede, configure o backend para aceitar conexões externas e informe o IP do servidor.

---

Se precisar de mais instruções ou personalização, consulte o desenvolvedor responsável.
