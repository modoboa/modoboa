tinyMCE.init({
    mode: "specific_textareas",
    editor_selector: "editor",
    theme: "advanced",
    plugins: "spellchecker,emotions",
    language: "{{ language }}",
    spellchecker_languages: "{{ spellchecker_languages }}",
    spellchecker_rpc_url: "{{ spellchecker_rpc_url }}",

    theme_advanced_toolbar_location: "top",
    theme_advanced_toolbar_align: "left",
    theme_advanced_buttons1: "bold,italic,underline,separator,justifyleft,justifycenter,justifyright,justifyfull,separator,bullist,numlist,indent,outdent,separator,undo,redo,separator,link,unlink,emotions,forecolor,backcolor,code,|,fontselect,fontsizeselect,spellchecker",
    theme_advanced_buttons2: "",
    theme_advanced_buttons3: ""
});