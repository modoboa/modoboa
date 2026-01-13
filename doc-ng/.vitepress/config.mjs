import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  // Use Canonical URL, but only the path and with no trailing /
  // End result is like: `/en/latest`
  // https://docs.readthedocs.com/platform/stable/intro/vitepress.html#using-the-proper-base-path
  base: process.env.READTHEDOCS_CANONICAL_URL
    ? new URL(process.env.READTHEDOCS_CANONICAL_URL).pathname.replace(/\/$/, '')
    : '',
  title: 'Modoboa',
  titleTemplate: ':title',
  description: 'Modoboa documentation',
  srcExclude: ['public/**/*.md'],
  ignoreDeadLinks: [/^https?:\/\/localhost:*/],
  metaChunk: true,
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      {
        text: 'Installation',
        items: [
          { text: 'Requirements', link: '/installation/requirements' },
          { text: 'Manual Installation', link: '/installation/manual' },
          { text: 'Modoboa Installer', link: '/installation/installer' },
          { text: 'Upgrade Instance', link: '/installation/upgrade' },
          { text: 'Configuration', link: '/configuration' },
        ],
      },
      {
        text: 'Contributing',
        items: [
          { text: 'Getting Started', link: '/contributing/getting_start' },
          { text: 'Write a Plugin', link: '/contributing/plugin_api' },
          { text: 'Translate', link: '/contributing/translation' },
          { text: 'Contributors', link: '/contributors' },
        ],
      },
    ],

    sidebar: {
      '/installation/': [
        {
          text: 'Manual',
          items: [
            { text: 'Modoboa', link: '/installation/modoboa' },
            { text: 'WebServer', link: '/installation/webserver' },
            { text: 'Dovecot', link: '/installation/dovecot' },
            { text: 'Postfix', link: '/installation/postfix' },
            { text: 'OpenDKIM', link: '/installation/opendkim' },
            { text: 'Radicale', link: '/installation/radicale' },
            { text: 'Amavis', link: '/installation/amavis' },
          ],
        },
        {
          text: 'Automatic',
          items: [
            { text: 'Modoboa Installer', link: '/installation/installer' },
          ],
        },
      ],
      '/contributing/': [
        { text: 'Getting Started', link: '/contributing/getting_start' },
        { text: 'Write a Plugin', link: '/contributing/plugin_api' },
        { text: 'Translate', link: '/contributing/translate' },
      ],
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/modoboa/modoboa' },
      { icon: 'discord', link: 'https://discord.gg/WuQ3v3PXGR' },
      {
        icon: {
          svg: `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                 <title>Transifex</title>
                 <path d="m20.073 12.851-2.758-2.757 3.722-3.659a.33.33 0 0 1 .467.003l2.27 2.309a.33.33 0 0 1-.004.468zm0 0h-.001zm-9.04-6.433 12.87 12.869c.129.13.129.34 0 .469l-2.289 2.289a.331.331 0 0 1-.468 0l-5.168-5.168-2.863 2.815c-.604.593-1.244 1.159-1.975 1.591a7.037 7.037 0 0 1-2.248.83c-2.191.42-4.557-.047-6.303-1.468A7.065 7.065 0 0 1 0 15.207V2.069a.33.33 0 0 1 .331-.33h3.237a.33.33 0 0 1 .331.33v4.125H6.65c.178 0 .323.145.323.323v3.617a.323.323 0 0 1-.323.323H3.899v4.75c0 1.272.808 2.429 1.988 2.893.753.295 1.617.321 2.397.131.852-.206 1.484-.717 2.097-1.319l2.839-2.792-4.945-4.945a.331.331 0 0 1 0-.468l2.289-2.289a.333.333 0 0 1 .469 0"/>
              </svg>`,
        },
        link: 'https://app.transifex.com/tonio/modoboa/dashboard/',
      },
      { icon: 'linkedin', link: 'https://www.linkedin.com/company/102575109' },
    ],
    footer: {
      message: 'Build with Vitepress',
      copyright: `Copyright © 2010-${new Date().getUTCFullYear()} Antoine Nguyen`,
    },
    outline: {
      label: 'Summmary',
    },
    docFooter: {
      prev: false,
      next: false,
    },
    search: {
      provider: 'local',
    },
    lastUpdated: {
      text: 'Update at',
      formatOptions: {
        dateStyle: 'full',
        timeStyle: 'short',
      },
    },
  },
  sitemap: {
    hostname: 'https://modoboa.readthedocs.io/en/latest',
  },
  markdown: {
    lineNumbers: true,
    image: {
      lazyLoading: true,
    },
  },
  cleanUrls: true,
  outDir: './dist',
  lastUpdated: true,
})
