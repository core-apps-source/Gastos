# Controle de Gastos

App web para registrar gastos em Pix, Crédito ou Débito.

## Como rodar

1. Instale as dependências:
   ```
   pip install flask
   ```

2. Rode o servidor:
   ```
   python app.py
   ```

3. Abra o navegador em: http://localhost:5000

Os dados ficam salvos em `gastos.db` (SQLite), criado automaticamente na primeira execução.

## Estrutura

```
gastos_app/
├── app.py              # Backend Flask (API + rotas)
├── gastos.db           # Banco de dados (criado automaticamente)
├── templates/
│   └── index.html      # Página principal
└── static/
    ├── style.css        # Estilos
    └── script.js        # Lógica do frontend (fetch na API)
```

## API

- `GET /api/gastos` — lista todos os gastos
- `POST /api/gastos` — cria um gasto `{descricao, valor, metodo, categoria, data}`
- `DELETE /api/gastos/<id>` — remove um gasto
- `GET /api/resumo` — retorna totais por método de pagamento
