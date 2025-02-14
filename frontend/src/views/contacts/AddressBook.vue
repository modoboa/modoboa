<template>
  <div class="text-h5 ml-4">
    {{ $gettext('Contacts') }}
  </div>
  <ContactList @edit-category="openCategoryForm" />
  <v-dialog v-model="showCategoryForm" persistent max-width="800px">
    <CategoryForm
      :category="contactsStore.currentCategory"
      @close="closeForm"
      @added="fetchCategories"
      @updated="fetchCategories"
    />
  </v-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useContactsStore, useLayoutStore } from '@/stores'
import contactsApi from '@/api/contacts'
import ContactList from '@/components/contacts/ContactList.vue'
import CategoryForm from '@/components/contacts/CategoryForm.vue'

const router = useRouter()
const { $gettext } = useGettext()
const contactsStore = useContactsStore()
const layoutStore = useLayoutStore()

const categories = ref([])
const showCategoryForm = ref(false)

const leftMenuItems = computed(() => {
  const result = [
    {
      icon: 'mdi-contacts',
      text: $gettext('Contacts'),
      to: { name: 'ContactList' },
    },
    {
      text: $gettext('Categories'),
      subheader: true,
    },
  ]
  for (const category of categories.value) {
    result.push({
      icon: 'mdi-label',
      text: category.name,
      action: () => filterByCategory(category),
    })
  }
  result.push({
    icon: 'mdi-plus',
    text: $gettext('Add a category'),
    action: openCategoryForm,
  })
  return result
})

function openCategoryForm() {
  showCategoryForm.value = true
}

function closeForm() {
  showCategoryForm.value = false
}

function filterByCategory(category) {
  contactsStore.setCurrentCategory(category)
  router.push({
    name: 'ContactList',
    params: {
      category: category.name,
    },
  })
}

function fetchCategories() {
  contactsApi.getCategories().then((resp) => {
    categories.value = resp.data
  })
}

fetchCategories()

watch(leftMenuItems, (value) => {
  layoutStore.setLeftMenuItems(value)
})
</script>
