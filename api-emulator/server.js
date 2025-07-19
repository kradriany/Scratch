const path = require('path');
const express = require('express');
const SwaggerUI = require('swagger-ui-express');
const OpenAPIBackend = require('openapi-backend').default;

// Load OpenAPI spec
const api = new OpenAPIBackend({ definition: path.join(__dirname, 'device-api.yaml') });

// Register handlers
api.register({
  // If no matching path+method
  notFound: (ctx, req, res) => {
    res.status(404).json({ error: 'Operation not found in spec' });
  },
  // For defined operations without a custom handler
  notImplemented: (ctx, req, res) => {
    const mock = ctx.api.mockResponseForOperation(req);
    res.status(mock.status || 200).json(mock.body);
  }
});
api.init();

const app = express();
app.use(express.json());

// Serve raw spec
app.get('/device-api.yaml', (req, res) => {
  res.sendFile(path.join(__dirname, 'device-api.yaml'));
});

// Serve Swagger UI
app.use(
  '/docs',
  SwaggerUI.serve,
  SwaggerUI.setup(null, { swaggerOptions: { url: '/device-api.yaml' } })
);

// Mock handler
app.use((req, res) => api.handleRequest(req, req, res));

const PORT = 3000;
app.listen(PORT, () => console.log(`API Emulator listening on http://localhost:${PORT}`));
