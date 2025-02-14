<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Address book information') }}</span>
    </v-card-title>
    <v-card-text>
      <p>
        {{
          $gettext(
            'To access this address book from the outside (such as Mozilla Thunderbird or your smartphone), use the following URL:'
          )
        }}
      </p>
      <v-alert type="info" class="my-4" variant="tonal">
        {{ addressBookUrl }}
      </v-alert>
      <p>
        {{
          $gettext(
            'The credentials are the same than the ones you use to access Modoboa.'
          )
        }}
      </p>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="$emit('close')">{{ $gettext('Close') }}</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
const props = defineProps({
  addressBookUrl: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close'])
</script>
