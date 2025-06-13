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
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import aliasesApi from '@/api/aliases'

const { $gettext } = useGettext()
const route = useRoute()

const alias = ref({ pk: route.params.id })

function refreshAlias() {
  aliasesApi.get(route.params.id).then((resp) => {
    alias.value = resp.data
  })
}

refreshAlias()
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
