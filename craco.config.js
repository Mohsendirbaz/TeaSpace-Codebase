const webpack = require('webpack');

module.exports = {
  devServer: function(devServerConfig) {
    // Remove the deprecated options
    delete devServerConfig.onBeforeSetupMiddleware;
    delete devServerConfig.onAfterSetupMiddleware;

    // Add the recommended setupMiddlewares option
    devServerConfig.setupMiddlewares = function(middlewares, devServer) {
      return middlewares;
    };

    return devServerConfig;
  },
  webpack: {
    configure: {
      resolve: {
        fallback: {
          "path": require.resolve("path-browserify"),
          "crypto": require.resolve("crypto-browserify"),
          "stream": require.resolve("stream-browserify"),
          "zlib": require.resolve("browserify-zlib"),
          "http": require.resolve("stream-http"),
          "fs": false,
          "net": false,
          "buffer": require.resolve("buffer/"),
          "util": require.resolve("util/"),
          "assert": require.resolve("assert/"),
          "url": require.resolve("url/"),
          "os": require.resolve("os-browserify/browser"),
          "https": require.resolve("https-browserify"),
          "constants": require.resolve("constants-browserify"),
          "vm": require.resolve("vm-browserify"),
          "tty": false,
          "child_process": false,
          "querystring": require.resolve("querystring-es3"),
          "async_hooks": false
        }
      },
      plugins: [
        // Add these plugins to provide empty implementations for Node.js core modules
        new webpack.ProvidePlugin({
          Buffer: ['buffer', 'Buffer'],
        }),
        new webpack.NormalModuleReplacementPlugin(/node:/, (resource) => {
          const mod = resource.request.replace(/^node:/, '');
          resource.request = mod;
        }),
        // Add IgnorePlugin to ignore the problematic express/lib/view.js module warnings
        new webpack.IgnorePlugin({
          resourceRegExp: /express\/lib\/view\.js$/,
          contextRegExp: /node_modules/,
        }),
      ],
      // Use stats configuration to suppress specific warnings
      stats: {
        warningsFilter: [
          /Critical dependency/,
          /express\/lib\/view\.js/,
        ],
      },
      ignoreWarnings: [
        // Ignore warnings about missing modules
        function ignoreSourcemapsloaderWarnings(warning) {
          return (
            warning.module &&
            (warning.module.resource.includes('node_modules/on-finished') ||
             warning.module.resource.includes('node_modules/raw-body') ||
             warning.module.resource.includes('node_modules/asn1.js'))
          );
        },
        // Ignore critical dependency warnings
        function ignoreCriticalDependencyWarnings(warning) {
          return (
            warning.message.includes('Critical dependency') &&
            warning.module &&
            warning.module.resource.includes('node_modules/express/lib/view.js')
          );
        },
        // Add a more general function to catch all critical dependency warnings
        function ignoreAllCriticalDependencyWarnings(warning) {
          return warning.message && warning.message.includes('Critical dependency');
        },
      ],
    }
  }
};
