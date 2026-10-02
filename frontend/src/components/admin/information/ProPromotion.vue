<template>
  <v-row>
    <v-col cols="12" md="7">
      <div
        class="text-overline text-secondary d-flex align-center font-weight-bold"
      >
        <v-icon icon="mdi-star-four-points" size="small" class="mr-1" />
        Modoboa Pro
      </div>
      <h3 class="text-h6 mb-2">
        {{ $gettext("Host your customers' email under their own brand") }}
      </h3>
      <p class="text-medium-emphasis mb-6">
        {{
          $gettext(
            'Modoboa Pro adds features for hosting providers, agencies and MSPs that manage several organizations from a single Modoboa instance.'
          )
        }}
      </p>
      <v-row dense>
        <v-col
          v-for="feature in features"
          :key="feature.icon"
          cols="12"
          sm="6"
          class="d-flex mb-2"
        >
          <v-avatar color="primary" variant="tonal" rounded size="36">
            <v-icon :icon="feature.icon" size="small" />
          </v-avatar>
          <div class="ml-3">
            <div class="font-weight-medium">{{ feature.title }}</div>
            <div class="text-body-small text-medium-emphasis">
              {{ feature.description }}
            </div>
          </div>
        </v-col>
      </v-row>
      <p class="text-body-small text-medium-emphasis mt-2">
        <v-icon
          icon="mdi-rocket-launch-outline"
          color="secondary"
          size="small"
          class="mr-1"
        />
        {{ $gettext('More features will come in upcoming releases.') }}
      </p>
      <div class="d-flex flex-wrap ga-2 mt-4">
        <v-btn
          :href="PRO_WEBSITE_URL"
          target="_blank"
          color="primary"
          variant="flat"
          append-icon="mdi-open-in-new"
        >
          {{ $gettext('Discover Modoboa Pro') }}
        </v-btn>
        <v-btn
          :href="PRO_INSTALL_GUIDE_URL"
          target="_blank"
          color="primary"
          variant="text"
          prepend-icon="mdi-book-open-variant-outline"
        >
          {{ $gettext('Installation guide') }}
        </v-btn>
      </div>
    </v-col>
    <v-col cols="12" md="5">
      <v-sheet color="grey-lighten-4" rounded class="pa-4 fill-height">
        <div class="font-weight-medium mb-3">{{ $gettext('Setup') }}</div>
        <ol class="steps text-body-medium text-medium-emphasis">
          <li>{{ $gettext('Install the modoboa-pro package.') }}</li>
          <li>
            {{
              $gettext(
                'Add the Modoboa Pro applications to MODOBOA_APPS and set MODOBOA_PRO_LICENSE_KEY in settings.py.'
              )
            }}
          </li>
          <li>
            {{
              $gettext(
                'Apply migrations and restart Modoboa: the installation registers itself automatically.'
              )
            }}
          </li>
        </ol>
        <v-divider class="my-3" />
        <div class="text-body-small text-medium-emphasis">
          {{ $gettext('You can hide this section in') }}
          <router-link
            :to="{ name: 'ParametersEdit', params: { app: 'core' } }"
          >
            {{ $gettext('Settings') }} › {{ $gettext('General') }}
          </router-link>
        </div>
      </v-sheet>
    </v-col>
  </v-row>
</template>

<script setup>
import { useGettext } from 'vue3-gettext'

const PRO_WEBSITE_URL = 'https://modoboa.com/'
const PRO_INSTALL_GUIDE_URL = 'https://doc.modoboa.com/guide/installation'

const { $gettext } = useGettext()

const features = [
  {
    icon: 'mdi-web',
    title: $gettext('Virtual hosts'),
    description: $gettext(
      'A public hostname per customer, served by the same instance.'
    ),
  },
  {
    icon: 'mdi-lock-outline',
    title: $gettext('Automatic HTTPS'),
    description: $gettext(
      "Let's Encrypt certificates issued and renewed automatically."
    ),
  },
  {
    icon: 'mdi-palette-outline',
    title: $gettext('Per-customer branding'),
    description: $gettext('Logos and colors specific to each hostname.'),
  },
  {
    icon: 'mdi-shield-lock-outline',
    title: $gettext('Customer isolation'),
    description: $gettext(
      "Each portal only gives access to its customer's domains."
    ),
  },
]
</script>

<style scoped lang="scss">
a:not(.v-btn) {
  text-decoration: none;
  color: rgb(var(--v-theme-primary));

  &:visited {
    color: rgb(var(--v-theme-primary));
  }
}

.steps {
  padding-left: 1.25rem;
}

.steps li + li {
  margin-top: 0.5rem;
}
</style>
