import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ConversionJob {
  job_id: string;
  file_id: string;
  filename: string;
  target_format: string;
  status: 'pending' | 'processing' | 'done' | 'failed';
  created_at: string;
  completed_at?: string;
  error_message?: string;
  download_url?: string;
}

interface ConversionState {
  jobs: ConversionJob[];
  currentJob: ConversionJob | null;
  
  // Actions
  addJob: (job: Omit<ConversionJob, 'status' | 'created_at'>) => void;
  updateJob: (jobId: string, updates: Partial<ConversionJob>) => void;
  removeJob: (jobId: string) => void;
  setCurrentJob: (job: ConversionJob | null) => void;
  clearHistory: () => void;
}

export const useConversionStore = create<ConversionState>()(
  persist(
    (set) => ({
      jobs: [],
      currentJob: null,

      addJob: (jobData) =>
        set((state) => ({
          jobs: [
            {
              ...jobData,
              status: 'pending',
              created_at: new Date().toISOString(),
            },
            ...state.jobs,
          ],
        })),

      updateJob: (jobId, updates) =>
        set((state) => ({
          jobs: state.jobs.map((job) =>
            job.job_id === jobId ? { ...job, ...updates } : job
          ),
          currentJob:
            state.currentJob?.job_id === jobId
              ? { ...state.currentJob, ...updates }
              : state.currentJob,
        })),

      removeJob: (jobId) =>
        set((state) => ({
          jobs: state.jobs.filter((job) => job.job_id !== jobId),
          currentJob:
            state.currentJob?.job_id === jobId ? null : state.currentJob,
        })),

      setCurrentJob: (job) => set({ currentJob: job }),

      clearHistory: () => set({ jobs: [] }),
    }),
    {
      name: 'conversion-storage',
      partialize: (state) => ({ jobs: state.jobs }),
    }
  )
);
