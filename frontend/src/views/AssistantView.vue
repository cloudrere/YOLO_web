<template>
  <AppLayout>
    <section class="assistant-shell panel-card">
      <div class="assistant-intro">
        <span class="eyebrow dark">独立问答模块</span>
        <h2>AI 助手</h2>
        <p>可接入 DeepSeek 或 OpenAI 兼容接口，用于说明检测结果、整理排查思路或回答系统使用问题。</p>
      </div>
      <el-tag :type="status?.configured ? 'success' : 'warning'">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
    </section>

    <section class="assistant-layout">
      <el-card shadow="never" class="panel-card assistant-chat-card">
        <template #header>提问</template>
        <el-input v-model="question" type="textarea" :rows="8" placeholder="请输入你的问题，例如：如何解释这批检测结果？" />
        <div class="form-actions assistant-actions">
          <el-button type="primary" :loading="loading" :disabled="!question.trim()" @click="send">发送问题</el-button>
          <el-button @click="question = ''">清空输入</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="panel-card assistant-answer-card">
        <template #header>回答</template>
        <div v-if="answer" class="assistant-answer">{{ answer }}</div>
        <el-empty v-else :description="status?.configured ? '发送问题后显示回答' : '后端未配置 AI_ASSISTANT_API_KEY，配置后即可使用'" />
      </el-card>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { askAssistant, getAssistantStatus, type AssistantStatus } from '@/api/assistant'

const status = ref<AssistantStatus | null>(null)
const question = ref('')
const answer = ref('')
const loading = ref(false)

async function loadStatus() {
  status.value = await getAssistantStatus()
}
async function send() {
  loading.value = true
  try {
    const data = await askAssistant(question.value)
    answer.value = data.answer
    status.value = { configured: data.configured, model: data.model }
  } finally {
    loading.value = false
  }
}
onMounted(loadStatus)
</script>
