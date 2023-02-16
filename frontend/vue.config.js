module.exports = {
  devServer: {
    proxy: {
      "/api": {
        target:
          process.env.DOCKER == "yes"
            ? "http://api:8000/"
            : "http://localhost:8000",
      },
    },
  },
  transpileDependencies: ["vuetify"],
  publicPath: process.env.NODE_ENV === "production" ? "/new-admin/" : "/",
  outputDir: "../modoboa/frontend_dist",
};
