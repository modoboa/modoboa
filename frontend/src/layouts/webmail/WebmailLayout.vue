<template>
  <ConnectedLayout>
    <template #navbar>
      <v-navigation-drawer
        v-model="drawer"
        :rail="rail"
        permanent
        color="primary"
        app
      >
        <div class="d-flex align-center">
          <v-img
            src="@/assets/Modoboa_RVB-BLANC-SANS.png"
            max-width="190"
            class="logo"
          />
          <v-btn
            :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
            variant="text"
            @click.stop="rail = !rail"
          >
          </v-btn>
        </div>

        <MailboxList
          :mailboxes="userMailboxes"
          class="mr-2"
          @mailbox-selected="openMailbox"
        />
      </v-navigation-drawer>
    </template>
  </ConnectedLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'
import MailboxList from '@/components/webmail/MailboxList.vue'
import api from '@/api/webmail'

const router = useRouter()

const drawer = ref(true)
const rail = ref(false)
const userMailboxes = ref([])

function openMailbox(mailbox) {
  console.log(mailbox)
  router.push({
    name: 'MailboxView',
    query: { mailbox: mailbox.name },
  })
}

api.getUserMailboxes().then((resp) => {
  userMailboxes.value = resp.data
})
</script>
