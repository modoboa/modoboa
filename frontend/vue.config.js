module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000/'
      }
    }
  },
  transpileDependencies: [
    'vuetify'
  ],
  publicPath: process.env.NODE_ENV === 'production'
    ? '/new-admin/'
    : '/',
  outputDir: '../modoboa/frontend_dist'
}
