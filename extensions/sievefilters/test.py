if __name__ == "__main__":
    clt = ManageSieveClient("mail.koalabs.org", 2000)
    if clt.connect("tonio@ngyn.org", "aka/12;c", starttls=True):
        print clt.get_sasl_mechanisms()
        print clt.get_sieve_capabilities()        
        print clt.havespace("test", 45)

        if not clt.putscript("myscript", """require ["fileinto", "envelope"];

if envelope :contains "to" "tmartin+sent" {
  fileinto "INBOX.sent";
}
"""):
            print clt.errmsg

        if not clt.putscript("test", """#comment
InvalidSieveCommand
"""):
            print clt.errmsg

        clt.deletescript("thescript")

        if not clt.setactive("myscript"):
            print clt.errmsg
        print clt.listscripts()

        sc = clt.getscript("myscript")
        if sc is None:
            print clt.errmsg
        else:
            print sc

        if not clt.renamescript("myscript", "thescript"):
            print clt.errmsg

        clt.setactive("")

        if not clt.deletescript("thescript"):
            print clt.errmsg
    else:
        print clt.errmsg
    clt.logout()

