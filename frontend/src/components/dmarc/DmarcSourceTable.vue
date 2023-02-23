<template>
<div>
  <div class="text-h6">{{ title }} <span :class="`${color}--text text--lighten-2`">{{ total }}</span></div>
  <v-simple-table>
    <tbody>
      <template v-for="(source, name) in sources">
        <tr :key="name">
          <th width="40%">{{ name }}</th>
          <th><translate>Total</translate></th>
          <th>SPF</th>
          <th>DKIM</th>
        </tr>
        <tr v-for="(counters, ip) in source" :key="ip">
          <td>{{ ip }}</td>
          <td>{{ counters.total }}</td>
          <td>
            <v-avatar
              color="green lighten-2"
              size="24"
              >
              <span class="white--text">{{ counters.spf.success }}</span>
            </v-avatar>
            <v-avatar
              color="red lighten-2 ml-1"
              size="24"
              >
              <span class="white--text">{{ counters.spf.failure }}</span>
            </v-avatar>
          </td>
          <td>
            <v-avatar
              color="green lighten-2"
              size="24"
              >
              <span class="white--text">{{ counters.dkim.success }}</span>
            </v-avatar>
            <v-avatar
              color="red lighten-2 ml-1"
              size="24"
              >
              <span class="white--text">{{ counters.dkim.failure }}</span>
            </v-avatar>
          </td>
        </tr>
      </template>
    </tbody>
  </v-simple-table>
</div>
</template>

<script>
export default {
  props: {
    title: String,
    color: String,
    total: Number,
    sources: Object
  }
}
</script>
