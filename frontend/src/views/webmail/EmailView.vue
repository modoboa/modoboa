<template>
  <div v-show="loaded" class="bg-white rounded-lg pa-4 mt-12">
    <v-toolbar color="white">
      <v-btn icon="mdi-arrow-left" size="small" variant="flat" @click="close" />

      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="mdi-reply"
        append-icon="mdi-chevron-down"
      >
        {{ $gettext('Reply') }}
        <v-menu activator="parent">
          <v-list>
            <v-list-item :title="$gettext('Reply all')" />
            <v-list-item :title="$gettext('Forward')" />
          </v-list>
        </v-menu>
      </v-btn>
      <v-btn
        class="ml-2"
        color="error"
        variant="tonal"
        icon="mdi-trash-can"
        size="small"
        :loading="working"
        @click="deleteEmail"
      >
      </v-btn>
      <v-btn
        v-if="$route.params.mailbox === 'Junk'"
        class="ml-2"
        color="warning"
        variant="tonal"
        icon="mdi-fire"
        size="small"
        :loading="working"
        @click="markEmailAsJunk"
      >
      </v-btn>
      <v-btn
        v-else
        class="ml-2"
        color="success"
        variant="tonal"
        icon="mdi-thumb-up"
        size="small"
        :loading="working"
        @click="markEmailAsNotJunk"
      >
      </v-btn>
      <v-btn class="ml-2" variant="tonal" icon size="small">
        <v-icon icon="mdi-cog" />
        <v-menu activator="parent">
          <v-list>
            <v-list-item
              v-if="!enableLinks"
              :title="$gettext('Enable links')"
              @click="enableLinks = true"
            />
            <v-list-item
              v-else
              :title="$gettext('Disable links')"
              @click="enableLinks = false"
            />
          </v-list>
        </v-menu>
      </v-btn>
    </v-toolbar>

    <div v-if="email" class="bg-white pa-4">
      <h2>{{ email.subject }}</h2>
      <div class="d-flex mt-2">
        <h3 v-if="email.from_address.fulladdress">
          {{ email.from_address.fulladdress }}
        </h3>
        <h3 v-else>{{ email.from_address.address }}</h3>
        <v-spacer />
        <span>{{ email.date }}</span>
      </div>
      <div class="mt-2">
        {{ $gettext('To') }}
        {{ recipients }}
      </div>
      <div v-if="email.attachments.length" class="mt-2">
        <v-icon icon="mdi-paperclip" />
        <template
          v-for="(attachment, index) in email.attachments"
          :key="attachment.name"
        >
          <template v-if="index > 0">, </template>
          <a
            href="#"
            @click="downloadAttachment(attachment.name, attachment.partnum)"
          >
            {{ attachment.name }}
          </a>
        </template>
      </div>
      <iframe class="email-frame" />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/webmail'

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()
const route = useRoute()
const router = useRouter()

const enableLinks = ref(false)
const email = ref(null)
const loaded = ref(false)
const working = ref(false)

const recipients = computed(() => {
  if (!email.value) {
    return ''
  }
  return email.value.to
    .map((rcpt) => (rcpt.name ? rcpt.name : rcpt.address))
    .join(', ')
})

onMounted(() => {
  fetchMailContent()
})

watch(enableLinks, () => {
  fetchMailContent()
})

const close = () => {
  router.push({
    name: 'MailboxView',
    query: { mailbox: route.query.mailbox },
  })
}

const fetchMailContent = () => {
  const options = {
    dformat: 'html',
    links: enableLinks.value ? '1' : '0',
  }
  api
    .getEmailContent(route.query.mailbox, route.query.mailid, options)
    .then((resp) => {
      email.value = resp.data
      nextTick(() => {
        const iframe = document.createElement('iframe')
        iframe.classList.add('email-frame')
        document.querySelector('iframe').replaceWith(iframe)
        const iframeDoc = iframe.contentDocument
        iframeDoc.write(email.value.body)
        iframeDoc.close()
        loaded.value = true
      })
    })
}

const downloadAttachment = (name, part) => {
  api
    .getEmailAttachment(route.query.mailbox, route.query.mailid, part)
    .then((resp) => {
      const blob = new Blob([resp.data], { type: resp.headers['Content-Type'] })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = name
      link.click()
      URL.revokeObjectURL(link.href)
    })
}

const deleteEmail = () => {
  working.value = true
  api.deleteSelection(route.query.mailbox, [route.query.mailid]).then(() => {
    working.value = false
    router.push({
      name: 'MailboxView',
      query: { mailbox: route.query.mailbox },
    })
    displayNotification({ msg: $gettext('Message deleted') })
  })
}

const markEmailAsJunk = () => {
  working.value = true
  api
    .markSelectionAsJunk(route.query.mailbox, [route.query.mailid])
    .then(() => {
      working.value = false
      router.push({
        name: 'MailboxView',
        query: { mailbox: route.query.mailbox },
      })
      displayNotification({ msg: $gettext('Message marked as junk') })
    })
}

const markEmailAsNotJunk = () => {
  working.value = true
  api
    .markSelectionAsNotJunk(route.query.mailbox, [route.query.mailid])
    .then(() => {
      working.value = false
      router.push({
        name: 'MailboxView',
        query: { mailbox: route.query.mailbox },
      })
      displayNotification({ msg: $gettext('Message marked as not junk') })
    })
}
</script>

<style>
.email-frame {
  width: 100%;
  min-height: 1000px;
  border: none;
  margin-top: 10px;
  background-color: #fff;
}
</style>
