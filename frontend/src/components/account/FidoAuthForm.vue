<template>
  <div>
    <v-card flat>
      <v-card-title>
        <span class="text-subtitle-1">
          {{ $gettext('WebAuthn') }}
        </span>
      </v-card-title>
      <v-card-text>
        <template v-if="fidoCreds.length === 0">
          <div tag="p" class="my-4">
            {{
              $gettext(
                "You don't have any WebAuthN registered as a second authentication method."
              )
            }}
          </div>
        </template>
        <template v-else>
          <h3>{{ $gettext("Registered Webauthn devices") }}</h3>
          <v-data-table-virtual
            :headers="headers"
            :items="fidoCreds"
            height="400"
            item-value="id"
          >
            <template #[`item.added_on`]="{ item }">
              {{ $date(item.added_on) }}
            </template>
            <template #[`item.last_used`]="{ item }">
              <template v-if="item.last_used === null">
                {{ $gettext('Never') }}
              </template>
              <template v-else>
                {{ $date(item.last_used) }}
              </template>
            </template>
            <template v-slot:item.actions="{ item }">
              <v-icon
                class="me-2"
                size="small"
                @click="editCred(item)"
              >
                mdi-pencil
              </v-icon>
              <v-icon
                size="small"
                @click="deleteCred(item)"
              >
                mdi-delete
              </v-icon>
            </template>
          </v-data-table-virtual>
        </template>
          <template v-if="browserCapable">
            <v-form ref="fidoForm" @submit.prevent="startFidoRegistration">
              <v-text-field
                v-model="name"
                :label="$gettext('Name')"
                :rules="[rules.required]"
              />
              <v-btn color="success" type="submit" :loading="registrationLoading">
                {{ $gettext('Add WebAuthN device') }}
              </v-btn>
            </v-form>
          </template>
          <template v-else>
            <v-alert type="error">
              {{ $gettext('Your browser does not seem compatible with WebAuthN') }}
            </v-alert>
          </template>
      </v-card-text>
    </v-card>
  </div>
   <ConfirmDialog ref="confirmDeletion"/>
   <ConfirmDialog ref="confirmEdition">
    <v-form ref="editForm">
      <v-text-field v-model="editName" :label="$gettext('name')"/>
      <v-switch v-model="editEnabled" :label="$gettext('enabled')" color="principal"/>
    </v-form>
   </ConfirmDialog>
</template>

<script setup lang="js">
import { ref, onMounted, computed } from 'vue'
import authApi from '@/api/auth.js'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules.js'
import { useAuthStore } from '@/stores'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const authStore = useAuthStore()

const { $gettext } = useGettext()

const name = ref()
const registrationLoading = ref(false)
const creationOption = ref()
const browserCapable = !!(navigator.credentials && navigator.credentials.create && navigator.credentials.get && window.PublicKeyCredential)
const fidoForm = ref()
const fidoCreds = computed(() => authStore.fidoCreds)
const headers = [
  { title: '#', key: 'id' },
  { title: $gettext('Name'), key: 'name' },
  { title: $gettext('Added On'), key: 'added_on' },
  { title: $gettext('Last Used'), key: 'last_used' },
  { title: $gettext('Use count'), key: 'use_count' },
  { title: $gettext('Enabled'), key: 'enabled' },
  { title: $gettext('Actions'), key: 'actions'}
]
const confirmDeletion = ref()
const confirmEdition = ref()
const editForm = ref()
const editName = ref('')
const editEnabled = ref(false)

async function startFidoRegistration() {
  const { valid } = await fidoForm.value.validate()
  if (!valid) {
    return
  }
  if (creationOption.value) {
    navigator.credentials.create({...creationOption.value})
      .then(function (attestation) {
        const result = createResponseToJSON(attestation)
        result.name = name.value
        authStore.addFidoCred(result)
      })
  }
}

async function deleteCred(cred) {
  const result = await confirmDeletion.value.open(
    $gettext('Warning'),
    $gettext('Do you really want to delete this WebaAuthn device?'),
    {
      color: 'warning',
      cancelLabel: $gettext('No'),
      agreeLabel: $gettext('Yes'),
    }
  )
  if (!result) {
    return
  }
  authStore.deleteFidoCreds(cred.id)
}

async function editCred(cred) {
  editName.value = cred.name
  editEnabled.value = cred.enabled
  const result = await confirmEdition.value.open(
  $gettext('Edition'),
    $gettext('Edit your device'),
    {
      color: 'warning',
      cancelLabel: $gettext('Cancel'),
      agreeLabel: $gettext('Save'),
    }
  )
  if (!result) {
    return
  }
  console.log(editForm.value.items)
}

onMounted(() => {
  registrationLoading.value = true
  authStore.getFidoCreds()
  authApi.beginFidoRegistration().then((resp) => {
    creationOption.value = createRequestFromJSON(resp.data)
  }).finally(() => registrationLoading.value = false)
})

// Taken from the example of python-fido2 repo
// src/webauthn-json/base64url.ts
function base64urlToBuffer(baseurl64String) {
  const padding = "==".slice(0, (4 - baseurl64String.length % 4) % 4);
  const base64String = baseurl64String.replace(/-/g, "+").replace(/_/g, "/") + padding;
  const str = atob(base64String);
  const buffer = new ArrayBuffer(str.length);
  const byteView = new Uint8Array(buffer);
  for (let i = 0; i < str.length; i++) {
    byteView[i] = str.charCodeAt(i);
  }
  return buffer;
}

function bufferToBase64url(buffer) {
  const byteView = new Uint8Array(buffer);
  let str = "";
  for (const charCode of byteView) {
    str += String.fromCharCode(charCode);
  }
  const base64String = btoa(str);
  const base64urlString = base64String.replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
  return base64urlString;
}

// src/webauthn-json/convert.ts
const copyValue = "copy";
const convertValue = "convert";
function convert(conversionFn, schema, input) {
  if (schema === copyValue) {
    return input;
  }
  if (schema === convertValue) {
    return conversionFn(input);
  }
  if (schema instanceof Array) {
    return input.map((v) => convert(conversionFn, schema[0], v));
  }
  if (schema instanceof Object) {
    const output = {};
    for (const [key, schemaField] of Object.entries(schema)) {
      if (schemaField.derive) {
        const v = schemaField.derive(input);
        if (v !== void 0) {
          input[key] = v;
        }
      }
      if (!(key in input)) {
        if (schemaField.required) {
          throw new Error(`Missing key: ${key}`);
        }
        continue;
      }
      if (input[key] == null) {
        output[key] = null;
        continue;
      }
      output[key] = convert(conversionFn, schemaField.schema, input[key]);
    }
    return output;
  }
}

function derived(schema, derive) {
  return {
    required: true,
    schema,
    derive
  };
}
function required(schema) {
  return {
    required: true,
    schema
  };
}
function optional(schema) {
  return {
    required: false,
    schema
  };
}

const publicKeyCredentialDescriptorSchema = {
  type: required(copyValue),
  id: required(convertValue),
  transports: optional(copyValue)
}

const simplifiedExtensionsSchema = {
  appid: optional(copyValue),
  appidExclude: optional(copyValue),
  credProps: optional(copyValue)
}

const simplifiedClientExtensionResultsSchema = {
  appid: optional(copyValue),
  appidExclude: optional(copyValue),
  credProps: optional(copyValue)
}

const credentialCreationOptions = {
  publicKey: required({
    rp: required(copyValue),
    user: required({
      id: required(convertValue),
      name: required(copyValue),
      displayName: required(copyValue)
    }),
    challenge: required(convertValue),
    pubKeyCredParams: required(copyValue),
    timeout: optional(copyValue),
    excludeCredentials: optional([publicKeyCredentialDescriptorSchema]),
    authenticatorSelection: optional(copyValue),
    attestation: optional(copyValue),
    extensions: optional(simplifiedExtensionsSchema)
  }),
  signal: optional(copyValue)
}

const publicKeyCredentialWithAttestation = {
  type: required(copyValue),
  id: required(copyValue),
  rawId: required(convertValue),
  authenticatorAttachment: optional(copyValue),
  response: required({
    clientDataJSON: required(convertValue),
    attestationObject: required(convertValue),
    transports: derived(copyValue, (response) => {
      var _a;
      return ((_a = response.getTransports) == null ? void 0 : _a.call(response)) || [];
    })
  }),
  clientExtensionResults: derived(simplifiedClientExtensionResultsSchema, (pkc) => pkc.getClientExtensionResults())
}

function createRequestFromJSON(requestJSON) {
  return convert(base64urlToBuffer, credentialCreationOptions, requestJSON);
}

function createResponseToJSON(credential) {
  return convert(bufferToBase64url, publicKeyCredentialWithAttestation, credential);
}

</script>
