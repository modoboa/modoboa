<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>
        {{ $gettext('Alias') }} {{ alias.address }}
        <v-btn
          color="primary"
          icon="mdi-circle-edit-outline"
          :to="{ name: 'AliasEdit', params: { id: alias.pk } }"
        />
        <v-btn color="primary" icon="mdi-reload" @click="refreshAlias()" />
      </v-toolbar-title>
    </v-toolbar>
    <v-row>
      <v-col cols="6">
        <AliasSummary :alias="alias" />
        <AliasRecipientsSummary :alias="alias" class="mt-2" />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="js">
import AliasRecipientsSummary from '@/components/admin/identities/AliasRecipientsSummary.vue'
import AliasSummary from '@/components/admin/identities/AliasSummary.vue'
import { useGettext } from 'vue3-gettext'
import { computed } from 'vue'
import { useAliasesStore } from '@/stores'
import { useRoute } from 'vue-router'

const { $gettext } = useGettext()
const aliasesStore = useAliasesStore()
const route = useRoute()

const alias = computed(() => {
  if (aliasesStore.aliases[route.params.id] !== undefined) {
    return aliasesStore.aliases[route.params.id]
  }
  refreshAlias()
  return { pk: route.params.id }
})

function refreshAlias() {
  aliasesStore.getAlias(route.params.id)
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
