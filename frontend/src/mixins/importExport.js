import { useBusStore } from '@/stores'

export const importExportMixin = () => {
  function exportContent(content, name, $gettext) {
    if (!content && !content.length) {
      const busStore = useBusStore()
      busStore.displayNotification({
        msg: $gettext('No data to export'),
        type: 'warning',
      })
      return
    }
    const blob = new Blob([content], { type: 'text/csv' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `modoboa-${name}.csv`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  function importContent(api, data, importForm, $gettext) {
    api
      .importFromCSV(data)
      .then((resp) => {
        const busStore = useBusStore()
        if (resp.data.status) {
          busStore.displayNotification({ msg: resp.data.message })
          importForm.value.close()
        } else {
          busStore.displayNotification({
            msg: resp.data.message,
            type: 'error',
          })
        }
      })
      .catch(() => {
        const busStore = useBusStore()
        busStore.displayNotification({
          msg: $gettext('CSV seems to be badly formatted'),
          type: 'error',
        })
      })
  }
  return { exportContent, importContent }
}
