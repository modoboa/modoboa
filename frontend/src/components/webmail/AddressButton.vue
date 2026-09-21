<template>
  <v-menu>
    <template #activator="{ props: menuProps }">
      <v-btn
        v-bind="menuProps"
        class="address-button"
        :class="{ 'address-button-strong': strong }"
        variant="text"
        size="small"
        :title="address.address"
      >
        <span class="address-button-label">{{ label }}</span>
      </v-btn>
    </template>
    <ContactCard :model-value="address" />
  </v-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '@/stores'
import ContactCard from '@/components/webmail/ContactCard.vue'

const props = defineProps({
  address: {
    type: Object,
    required: true,
  },
  // The sender weighs more than the recipients
  strong: {
    type: Boolean,
    default: false,
  },
})

const { $gettext } = useGettext()
const authStore = useAuthStore()

const isOwnAddress = computed(() => {
  const user = authStore.authUser
  const address = props.address.address?.toLowerCase()
  return [user?.mailbox?.full_address, user?.username]
    .filter(Boolean)
    .some((own) => own.toLowerCase() === address)
})

const label = computed(() =>
  isOwnAddress.value
    ? $gettext('Me')
    : props.address.name || props.address.address
)
</script>
