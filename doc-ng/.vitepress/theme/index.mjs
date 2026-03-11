import DefaultTheme from 'vitepress/theme';
import { theme, useOpenapi } from 'vitepress-openapi/client';
import 'vitepress-openapi/dist/style.css';
import spec from '../../openapi.json';

export default {
  ...DefaultTheme,
  async enhanceApp({ app, router, siteData }) {
    const openapi = useOpenapi({
      spec,
      config: {},
    });

    theme.enhanceApp({ app, openapi });
  },
};