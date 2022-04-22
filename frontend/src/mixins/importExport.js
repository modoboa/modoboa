import { bus } from '@/main'

export const importExportMixin = {
  methods: {
    exportContent (content, name) {
      const blob = new Blob([content], { type: 'text/csv' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `modoboa-${name}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
    },
    importContent (api, data) {
      api.importFromCSV(data).then(resp => {
        if (resp.data.status) {
          bus.$emit('notification', { msg: resp.data.message })
          this.$refs.importForm.close()
        } else {
          bus.$emit('notification', { msg: resp.data.message, type: 'error' })
        }
      })
    }
  }
}
