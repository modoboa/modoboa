<template>
  <div>
    <div class="text-h6">
      {{ title }}
      <span :class="text - `${color}-lighten-2`">{{ total }}</span>
    </div>
    <v-simple-table>
      <tbody>
        <template v-for="(source, name) in sources" :key="name">
          <tr>
            <th width="40%">{{ name }}</th>
            <th>{{ $gettext('Total') }}</th>
            <th>SPF</th>
            <th>DKIM</th>
          </tr>
          <tr v-for="(counters, ip) in source" :key="ip">
            <td>{{ ip }}</td>
            <td>{{ counters.total }}</td>
            <td>
              <v-avatar color="green lighten-2" size="24">
                <span class="text-white">{{ counters.spf.success }}</span>
              </v-avatar>
              <v-avatar color="red lighten-2 ml-1" size="24">
                <span class="text-white">{{ counters.spf.failure }}</span>
              </v-avatar>
            </td>
            <td>
              <v-avatar color="green lighten-2" size="24">
                <span class="text-white">{{ counters.dkim.success }}</span>
              </v-avatar>
              <v-avatar color="red lighten-2 ml-1" size="24">
                <span class="text-white">{{ counters.dkim.failure }}</span>
              </v-avatar>
            </td>
          </tr>
        </template>
      </tbody>
    </v-simple-table>
  </div>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
const { $gettext } = useGettext()
defineProps({
  title: { type: String, default: '' },
  color: { type: String, default: '' },
  total: { type: Number, default: null },
  sources: { type: Object, default: null },
})
</script>
