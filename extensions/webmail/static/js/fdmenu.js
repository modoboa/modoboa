/*
 * Simple dropdown menu plugin used for folders manipulation.
 *
 */
var FdMenu = new Class({
    Implements: [Options],

    options: {
      modify_url: "",
      delete_url: ""
    },

    add_entry: function(name, label, pic, url, onclick) {
      var item = new Element("li");
      var picpath = static_url("pics/" + pic);

      this[name] = new Element("a")
        .set("html", "<img src='" + picpath + "' /> " + label)
        .addEvent("click", onclick.bind(this))
        .inject(item);
      item.inject(this.list);
    },

    initialize: function(options) {
      this.setOptions(options);

      this.container = new Element("div", {"id" : "fdmenu"})
        .addClass("fdmenu");
      this.list = new Element("ul");

      this.add_entry("modbutton", gettext("Edit folder"),
        "edit.png", this.options.modify_url, function(evt) {
          evt.stop();
          SqueezeBox.initialize({
            size: {x: 350, y: 400},
            handler: 'iframe'
          });
          SqueezeBox.open(evt.target.get("href"));
          $(document.body).fireEvent("click");
        });
      this.add_entry("delbutton", gettext("Delete folder"), "remove.png",
        this.options.delete_url, function(evt) {
          evt.stop();
          $(document.body).fireEvent("click");
          if (!confirm(gettext("Delete folder?"))) {
            return;
          }
          new Request.JSON({
            url: evt.target.get("href"),
            method: "GET",
            onSuccess: function(resp) {
              if (resp.status == "ok") {
                var dfolder = this.current_folder + "/";
                infobox.info(gettext("Folder deleted."));
                if (dfolder == current_anchor.base) {
                  var pfolder = ((this.current_folder.split(".")).slice(0, -1)).join(".");
                  if (pfolder == "") {
                    pfolder = "INBOX";
                  }
                  current_anchor.baseurl(pfolder, 1);
                }
                current_anchor.update.delay(500, current_anchor, 1);
              } else {
                infobox.error(gettext("Failed to delete folder"));
                infobox.hide(2);
              }
            }.bind(this)
          }).send();
        }
      );
      this.list.inject(this.container);
      this.shown = false;

      $(document.body).addEvent("click", function() {
        if (this.shown) {
          this.hide();
        }
      }.bind(this));
      //this.fx = new Fx.Slide(this.container);
    },

    show: function(origin, folder) {
      var position = origin.getPosition();

      this.container.setStyles({
          position: "absolute",
          top: position.y + 5,
          left: position.x + 5,
          display: "block"
      });
      this.container.inject(document.body);
      this.shown = true;
      this.current_folder = folder;
      this.modbutton.set("href", this.options.modify_url + "?name=" + folder);
      this.delbutton.set("href", this.options.delete_url + "?name=" + folder);
    },

    hide: function() {
      this.container.setStyles({
        display: "none"
      });
      this.container.dispose();
      this.shown = false;
    },

    toggle: function(origin, folder) {
      return (!this.shown) ? this.show(origin, folder) : this.hide();
    }
});