<template>
  <div>
    <v-card flat>
      <v-card-title>
        <span class="text-subtitle-1">
          {{ $gettext('WebAuthn') }}
        </span>
      </v-card-title>
      <v-card-text>
        <div tag="p" class="my-4">
            {{
              $gettext(
                "You don't have any WebAuthN registered as a second authentication method."
              )
            }}
          </div>
          <template v-if="browserCapable">
            <v-text-field v-model="name" />
            <v-btn color="success" :loading="registrationLoading" @click="startFidoRegistration">
              {{ $gettext('Add WebAuthN device') }}
            </v-btn>
          </template>
          <template v-else>
            <v-alert type="error">
              {{ $gettext('Your browser does not seem compatible with WebAuthN') }}
            </v-alert>
          </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="js">
import { ref, onMounted } from 'vue'
import authApi from '@/api/auth.js'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()

const name = ref()
const registrationLoading = ref(false)
const creationOption = ref()
const browserCapable = !!(navigator.credentials && navigator.credentials.create && navigator.credentials.get && window.PublicKeyCredential)

async function startFidoRegistration() {
  if (creationOption.value) {
    navigator.credentials.create({...creationOption.value})
      .then(function (attestation) {
        const result = createResponseToJSON(attestation)
        console.log(result)
      })
  }
}

onMounted(() => {
  registrationLoading.value = true
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
