<template>
  <v-card v-if="calendar">
    <v-card-title>
      <span class="headline">{{ $gettext('Calendar information') }}</span>
    </v-card-title>
    <v-card-text>
      <p>
        {{
          $gettext(
            'To access this calendar from the outside (such as Mozilla Thunderbird or your smartphone), use the following URL:'
          )
        }}
      </p>
      <v-alert type="info" class="my-4" variant="tonal">
        {{ calendar.full_url }}
      </v-alert>
      <p>
        {{
          $gettext(
            'The credentials are the same than the ones you use to access Modoboa.'
          )
        }}
      </p>
      <p>
        {{
          $gettext(
            'You can also share a read-only version of this calendar using the following URL: '
          )
        }}
      </p>
      <v-alert type="info" class="my-4" variant="tonal">
        {{ calendar.share_url }}
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="$emit('close')">{{ $gettext('Close') }}</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
const props = defineProps({
  calendar: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close'])
</script>
