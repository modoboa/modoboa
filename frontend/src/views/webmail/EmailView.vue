<template>
  <div v-show="loaded" class="bg-white rounded-lg pa-4 position-relative h-100">
    <v-toolbar color="white">
      <v-btn icon="mdi-arrow-left" size="small" variant="flat" @click="close" />

      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="mdi-reply"
        @click="() => replyToEmail()"
      >
        {{ $gettext('Reply') }}
        <template #append>
          <v-btn size="x-small" variant="plain">
            <v-icon icon="mdi-chevron-down" />
            <v-menu activator="parent">
              <v-list>
                <v-list-item
                  :title="$gettext('Reply all')"
                  @click="() => replyToEmail(true)"
                />
                <v-list-item
                  :title="$gettext('Forward')"
                  @click="forwardEmail"
                />
              </v-list>
            </v-menu>
          </v-btn>
        </template>
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
        v-if="route.params.mailbox !== 'Junk'"
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
          <v-list density="compact">
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
            <v-list-item
              :title="$gettext('Display source')"
              @click="openEmailSourceDialog"
            />
          </v-list>
        </v-menu>
      </v-btn>
    </v-toolbar>

    <div v-if="email" ref="headers" class="bg-white pa-4">
      <h2>{{ email.subject }}</h2>
      <div class="d-flex mt-2">
        <v-menu key="sender">
          <template #activator="{ props }">
            <h3 v-bind="props">
              <template v-if="email.from_address.name">
                {{ email.from_address.name }}
                <span class="text-grey text-body-2">
                  &lt;{{ email.from_address.address }}&gt;
                </span>
              </template>
              <template v-else>
                {{ email.from_address.address }}
              </template>
            </h3>
          </template>
          <ContactCard v-model="email.from_address" />
        </v-menu>
        <v-spacer />
        <span class="text-grey">{{ email.date }}</span>
      </div>
      <div class="mt-2 text-grey">
        {{ $gettext('To') }}
        <v-menu v-for="(rcpt, index) in email.to" :key="`to-${index}`">
          <template #activator="{ props }">
            <span v-if="index > 0">, </span>
            <span v-bind="props">{{ rcpt.name || rcpt.address }}</span>
          </template>
          <ContactCard v-model="email.to[index]" />
        </v-menu>
        <template v-if="email.cc?.length">
          <v-menu v-for="(rcpt, index) in email.cc" :key="`cc-${index}`">
            <template #activator="{ props }">
              <span>, </span>
              <span v-bind="props">{{ rcpt.name || rcpt.address }}</span>
            </template>
            <ContactCard v-model="email.cc[index]" />
          </v-menu>
        </template>
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
    </div>
    <iframe class="email-frame" />
  </div>
  <v-dialog v-model="showEmailSource" max-width="1200">
    <v-card :title="$gettext('Message source')">
      <v-card-text class="text-caption overflow-x-auto">
        <pre>{{ emailSource }}</pre>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          :text="$gettext('Close')"
          @click="showEmailSource = false"
        ></v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/webmail'
import ContactCard from '@/components/webmail/ContactCard.vue'

const { $gettext } = useGettext()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const route = useRoute()
const router = useRouter()

const enableLinks = ref(false)
const email = ref(null)
const emailSource = ref(null)
const headers = ref(null)
const loaded = ref(false)
const showEmailSource = ref(false)
const working = ref(false)

onMounted(() => {
  window.addEventListener('resize', resizeEmailIframe)
  fetchMailContent()
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeEmailIframe)
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

const resizeEmailIframe = () => {
  const iframe = document.querySelector('iframe')
  const rect = headers.value.getBoundingClientRect()
  iframe.style.top = `${rect.bottom}px`
  iframe.style.width = `${rect.width - 24}px`
  iframe.style.height = `${window.innerHeight - rect.bottom - 32}px`
}

const fetchMailContent = () => {
  const options = {
    dformat: 'html',
    links: enableLinks.value ? '1' : '0',
  }
  api
    .getEmailContent(route.query.mailbox, route.query.mailid, options)
    .then((resp) => {
      reloadMailboxCounters()
      email.value = resp.data
      nextTick(() => {
        const iframe = document.createElement('iframe')
        iframe.classList.add('email-frame')
        document.querySelector('iframe').replaceWith(iframe)
        const iframeDoc = iframe.contentDocument
        iframeDoc.write(email.value.body)
        iframeDoc.close()
        loaded.value = true
        nextTick(resizeEmailIframe)
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

const openEmailSourceDialog = async () => {
  if (!emailSource.value) {
    const resp = await api.getEmailSource(
      route.query.mailbox,
      route.query.mailid
    )
    emailSource.value = resp.data.source
  }
  showEmailSource.value = true
}

const replyToEmail = (all) => {
  const query = { ...route.query }
  if (all) {
    query.all = all
  }
  router.push({ name: 'ReplyEmailView', query })
}

const forwardEmail = () => {
  router.push({ name: 'ForwardEmailView', query: route.query })
}
</script>

<style>
.email-frame {
  position: absolute !important;
  left: 24px;
  overflow-y: auto;
  border: none;
  background-color: #fff;
}
</style>
