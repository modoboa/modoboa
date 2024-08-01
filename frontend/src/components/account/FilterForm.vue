<template>
  <v-card :title="title">
    <v-card-text>
      <v-form ref="formRef">
        <v-text-field
          v-model="form.name"
          :label="$gettext('Name')"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
          :error-messages="apiErrors.name ? apiErrors.name : []"
        />
        <div class="bg-grey-lighten-4 rounded pa-3">
          <h4>{{ $gettext('Conditions') }}</h4>
          <v-radio-group v-model="form.match_type" color="primary" inline>
            <v-radio :label="$gettext('All of the following')" value="allof" />
            <v-radio :label="$gettext('Any of the following')" value="anyof" />
            <v-radio :label="$gettext('All messages')" value="all" />
          </v-radio-group>
          <template v-if="form.match_type !== 'all'">
            <div
              v-for="(condition, index) in form.conditions"
              :key="`condition-${index}`"
              class="d-flex align-start"
            >
              <v-select
                v-model="condition.name"
                :label="$gettext('Choose a header')"
                :items="conditionTemplates"
                item-title="label"
                item-value="name"
                variant="outlined"
                density="compact"
                :rules="[rules.required]"
              />
              <v-select
                v-model="condition.operator"
                :label="$gettext('Choose an operator')"
                :items="getConditionOperators(condition.name)"
                item-title="label"
                item-value="name"
                variant="outlined"
                class="ml-2"
                density="compact"
                :rules="[rules.required]"
              />
              <v-text-field
                v-model="condition.value"
                :label="$gettext('Value')"
                variant="outlined"
                class="ml-2"
                density="compact"
                :type="getConditionType(index)"
                :rules="[rules.required]"
              />
              <v-btn
                v-if="index === 0"
                icon="mdi-plus"
                variant="text"
                :title="$gettext('Add condition')"
                color="primary"
                @click="addCondition"
              />
              <v-btn
                v-else
                icon="mdi-trash-can"
                variant="text"
                :title="$gettext('Remove condition')"
                color="error"
                @click="removeCondition(index)"
              />
            </div>
          </template>
        </div>
        <div class="mt-4 bg-grey-lighten-4 rounded pa-3">
          <h4>{{ $gettext('Actions') }}</h4>
          <div
            v-for="(action, index) in form.actions"
            :key="`action-${index}`"
            class="d-flex align-start mt-2"
          >
            <v-select
              v-model="action.name"
              :label="$gettext('Choose an action')"
              :items="actionTemplates"
              item-title="label"
              item-value="name"
              variant="outlined"
              density="compact"
              class="flex-grow-0"
            />
            <div class="mx-2 d-flex flex-column flex-grow-1">
              <template
                v-for="(arg, argIndex) in getActionArguments(action.name)"
                :key="`arg-${index}-${argIndex}`"
              >
                <v-select
                  v-if="arg.type === 'list'"
                  v-model="action.args[arg.name]"
                  :items="arg.choices"
                  item-title="label"
                  density="compact"
                  variant="outlined"
                  :rules="[rules.required]"
                />
                <v-text-field
                  v-if="arg.type === 'string'"
                  v-model="action.args[arg.name]"
                  density="compact"
                  variant="outlined"
                  :rules="[rules.required]"
                />
                <v-checkbox
                  v-if="arg.type === 'boolean'"
                  v-model="action.args[arg.name]"
                  :label="arg.label"
                  color="primary"
                  :value="arg.value"
                  density="compact"
                />
              </template>
            </div>
            <v-btn
              v-if="index === 0"
              icon="mdi-plus"
              variant="text"
              :title="$gettext('Add action')"
              color="primary"
              @click="addAction"
            />
            <v-btn
              v-else
              icon="mdi-trash-can"
              variant="text"
              :title="$gettext('Remove action')"
              color="error"
              @click="removeAction(index)"
            />
          </div>
        </div>
      </v-form>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        :text="$gettext('Cancel')"
        variant="elevated"
        @click="close"
      ></v-btn>
      <v-btn
        color="primary"
        variant="elevated"
        :text="submitLabel"
        :loading="working"
        @click="submit"
      ></v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import accountApi from '@/api/account'
import rules from '@/plugins/rules'

const props = defineProps({
  filterSet: {
    type: String,
    default: null,
  },
  filter: {
    type: Object,
    required: false,
    default: null,
  },
})
const emit = defineEmits(['close'])
const busStore = useBusStore()
const { $gettext } = useGettext()

const apiErrors = ref({})
const conditionTemplates = ref([])
const actionTemplates = ref([])
const formRef = ref()
const form = ref(getInitialFormContent())
const working = ref(false)

const title = computed(() => {
  return props.filter ? $gettext('Edit filter') : $gettext('New filter')
})
const submitLabel = computed(() => {
  return props.filter ? $gettext('Update') : $gettext('Create')
})

let originalFilterName

watch(
  () => props.filter,
  (value) => {
    if (value) {
      form.value = JSON.parse(JSON.stringify(value))
      originalFilterName = value.name
    } else {
      form.value = getInitialFormContent()
    }
  },
  { immediate: true }
)

function close() {
  emit('close')
  form.value = getInitialFormContent()
}

function getInitialFormContent() {
  return {
    match_type: 'anyof',
    conditions: [{}],
    actions: [
      {
        args: {},
      },
    ],
  }
}

function getConditionOperators(condition) {
  for (const template of conditionTemplates.value) {
    if (template.name === condition) {
      return template.operators
    }
  }
  return []
}

function getConditionType(index) {
  for (const template of conditionTemplates.value) {
    if (template.name === form.value.conditions[index].name) {
      for (const operator of template.operators) {
        if (operator.name === form.value.conditions[index].operator) {
          return operator.type === 'string' ? 'text' : 'number'
        }
      }
    }
  }
}

function getActionArguments(action) {
  for (const template of actionTemplates.value) {
    if (template.name === action) {
      return template.args
    }
  }
  return []
}

function addCondition() {
  form.value.conditions.push({
    name: conditionTemplates.value[0].name,
    operator: conditionTemplates.value[0].operators[0].name,
  })
}

function removeCondition(index) {
  form.value.conditions.splice(index, 1)
}

function addAction() {
  form.value.actions.push({
    name: actionTemplates.value[0].name,
    args: {},
  })
}

function removeAction(index) {
  form.value.actions.splice(index, 1)
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  let msg
  const data = JSON.parse(JSON.stringify(form.value))
  for (const action of data.actions) {
    for (const [key, value] of Object.entries(action.args)) {
      if (typeof value === 'boolean' && !value) {
        delete action.args[key]
      }
    }
  }
  try {
    if (!props.filter) {
      await accountApi.createFilter(props.filterSet, data)
      msg = $gettext('Filter added')
    } else {
      await accountApi.updateFilter(props.filterSet, originalFilterName, data)
      msg = $gettext('Filter updated')
    }
  } catch (err) {
    if (err.response.status === 400 && err.response.data) {
      apiErrors.value = err.response.data
    }
    return
  } finally {
    working.value = false
  }
  busStore.displayNotification({ msg })
  close()
}

accountApi.getFilterConditionTemplates().then((resp) => {
  conditionTemplates.value = resp.data
  if (!props.filter) {
    form.value.conditions[0].name = conditionTemplates.value[0].name
    form.value.conditions[0].operator =
      conditionTemplates.value[0].operators[0].name
  }
})
accountApi.getFilterActionTemplates().then((resp) => {
  actionTemplates.value = resp.data
  if (!props.filter) {
    form.value.actions[0].name = actionTemplates.value[0].name
  }
})
</script>
