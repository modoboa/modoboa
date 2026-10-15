import pluginVue from 'eslint-plugin-vue'
import eslintConfigPrettier from 'eslint-config-prettier'

export default [
  // A config object holding only `ignores` applies to every file (global
  // ignores); inside an object that also has rules it would only scope that
  // object.
  {
    ignores: ['node_modules/**', 'dist/**', 'coverage/**', 'storybook-static/**'],
  },
  ...pluginVue.configs['flat/recommended'],
  eslintConfigPrettier,
  {
    rules: {
      'vue/component-name-in-template-casing': [
        'error',
        'PascalCase',
        {
          registeredComponentsOnly: true,
          ignores: [],
        },
      ],
    },
  },
]
