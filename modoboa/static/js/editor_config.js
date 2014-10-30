CKEDITOR.editorConfig = function(config) {
    config.allowedContent = true;
    config.toolbar = "Modoboa";
    config.toolbar_Modoboa = [
        ['Bold','Italic','Underline'],
        ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
        ['NumberedList','BulletedList','-','Outdent','Indent'],
        ['Undo','Redo'],
        ['Link','Unlink','Anchor','-','Smiley'],
        ['TextColor','BGColor','-','Source'],
        ['Font','FontSize'],
        ['SpellChecker']
    ];
};
