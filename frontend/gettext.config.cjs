module.exports = {
  output: {
    flat: false,
    path: './src/locale',
    // No msgmerge fuzzy guesses: they pair new msgids with unrelated old
    // translations ("Reading pane" -> "Agendamento atualizado"). New strings
    // must arrive empty and be translated deliberately.
    fuzzyMatching: false,
    locales: [
      'en',
      'br',
      'cs',
      'de',
      'el',
      'es',
      'fi',
      'fr',
      'it',
      'ja',
      'nl',
      'pl',
      'pt_BR',
      'ru',
      'sv',
      'tr',
      'zh',
    ],
  },
}
