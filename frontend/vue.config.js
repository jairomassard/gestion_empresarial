const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  // Eliminamos configureWebpack por ahora para evitar conflictos
});
