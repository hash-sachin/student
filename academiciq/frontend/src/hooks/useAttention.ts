import { useQuery, useMutation } from '@tanstack/react-query'
import { intelligenceApi } from '@/api/endpoints'

export function useAttentionList(examinationId: string, band?: string) {
  return useQuery({
    queryKey: ['attention', examinationId, band],
    queryFn: () => intelligenceApi.attention(examinationId, band).then(r => r.data),
    enabled: !!examinationId,
  })
}

export function useComputeAttention() {
  return useMutation({
    mutationFn: ({
      studentId,
      examinationId,
      sectionId,
    }: {
      studentId: string
      examinationId: string
      sectionId?: string
    }) =>
      intelligenceApi
        .computeAttention(studentId, examinationId, sectionId)
        .then(r => r.data),
  })
}
