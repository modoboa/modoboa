import { usePaths } from 'vitepress-openapi'
import spec from '../openapi.json' with { type: 'json' }

export default {
  paths() {
    return usePaths({ spec })
      .getTags()
      .map(({ name }) => {
        return {
          params: {
            tag: name,
            pageTitle: `${name} - modoboa-openapi`,
          },
        }
      })
  },
}
