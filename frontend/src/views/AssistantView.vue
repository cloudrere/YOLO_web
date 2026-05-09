<template>
  <AppLayout>
    <section class="workstation-hero">
      <div>
        <h2>AI 检测助手</h2>
        <p>内置目标检测领域专家：解答检测结果、模型训练、设备配置与日志排查问题。</p>
      </div>
      <el-tag :type="status?.configured ? 'success' : 'warning'">{{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}</el-tag>
    </section>

    <!-- 助手双栏布局 -->
    <section class="assistant-layout">
      <!-- 左栏：预设问题分类 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">常用问题</span></template>
        <p class="text-muted" style="margin:0 0 12px;">选择预设提示词快速开始，也可直接输入问题。</p>
        <div style="display:grid;gap:6px;">
          <el-button v-for="item in prompts" :key="item.label" @click="question = item.question" style="justify-content:flex-start;padding:10px 12px;height:auto;border-radius:8px;text-align:left;">
            <div>
              <strong style="display:block;font-size:13px;">{{ item.label }}</strong>
              <span style="display:block;font-size:11px;color:var(--color-muted);margin-top:2px;">{{ item.question }}</span>
            </div>
          </el-button>
        </div>
        <div style="margin-top:16px;padding:14px;border-radius:var(--radius-md);background:#eff6ff;border:1px solid #bfdbfe;">
          <span style="display:block;font-size:11px;color:var(--color-muted);">服务状态</span>
          <strong style="display:block;color:var(--color-primary-deep);font-size:18px;margin-top:4px;">{{ status?.configured ? '可用' : '未配置' }}</strong>
          <small style="display:block;color:var(--color-muted);margin-top:4px;">{{ status?.model || '等待配置 AI_ASSISTANT_API_KEY' }}</small>
        </div>
      </el-card>

      <!-- 右栏：问答会话 -->
      <el-card shadow="never">
        <template #header><span style="font-weight:700;">对话</span></template>
        <div class="chat-conversation">
          <div class="chat-bubble assistant">
            <strong style="display:block;margin-bottom:4px;">AI 检测助手</strong>
            <p style="margin:0;">我可以帮你解释检测结果、分析模型训练质量、排查 GPU/CUDA 设备问题、或回答系统使用问题。请直接输入问题。</p>
          </div>
          <template v-for="message in messages" :key="message.id">
            <div class="chat-bubble user">
              <strong style="display:block;margin-bottom:4px;">你</strong>
              <p style="margin:0;">{{ message.question }}</p>
            </div>
            <div class="chat-bubble assistant">
              <strong style="display:block;margin-bottom:4px;">AI 助手</strong>
              <p style="margin:0;">{{ message.answer }}</p>
            </div>
          </template>
          <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话' : '后端未配置 API Key，配置后即可使用'" />
        </div>
        <div style="margin-top:12px;padding:12px;border-radius:var(--radius-md);background:var(--color-bg);border:1px solid var(--color-border);">
          <el-input v-model="question" type="textarea" :rows="4" placeholder="请输入问题，例如：如何解释这批检测结果中低置信度目标？" @keyup.ctrl.enter="send" />
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;">
            <el-button size="small" @click="question = ''">清空</el-button>
            <el-button type="primary" size="small" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">发送 (Ctrl+Enter)</el-button>
          </div>
        </div>
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
const loading = ref(false)
const messages = ref<Array<{ id: number; question: string; answer: string }>>([])

const prompts = [
  { label: '检测结果分析', question: '如何解读检测结果中的类别分布和置信度？低置信度目标应该如何处理？' },
  { label: 'GPU 设备排查', question: '如何排查 CUDA out of memory 错误？有哪些优化显存使用的方法？' },
  { label: '模型训练建议', question: 'YOLO 训练过程中 loss 不下降或震荡严重，可能是什么原因？如何调整超参数？' },
  { label: '实时流优化', question: '实时视频流检测延迟过高，如何在不牺牲精度的情况下提高 FPS？' },
  { label: '类别映射维护', question: '如何为训练好的 YOLO 模型维护中英文类别映射？需要重新训练吗？' },
]

async function loadStatus() { status.value = await getAssistantStatus() }
async function send() {
  const text = question.value.trim(); if (!text) return
  loading.value = true
  try { const data = await askAssistant(text); messages.value.push({ id: Date.now(), question: text, answer: data.answer }); status.value = { configured: data.configured, model: data.model }; question.value = '' } finally { loading.value = false }
}
onMounted(loadStatus)
</script>
