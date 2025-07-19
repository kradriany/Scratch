# MCP MVP

This repository contains a minimal setup for a local MCP platform composed of:

- **api-emulator**: Mock device API with Swagger UI
- **agent-service**: Polls the emulator every 5 seconds
- **kong**: Gateway for routing requests
- **zeek**: Network sensor monitoring Kong traffic

Start all services:

```bash
docker-compose up --build -d
```

Access points:

- Swagger UI: [http://localhost:3000/docs](http://localhost:3000/docs)
- Kong proxy: [http://localhost:8000/api/status](http://localhost:8000/api/status)
- Agent logs: `docker logs -f agent-service`
- Zeek logs: `docker logs -f zeek`

