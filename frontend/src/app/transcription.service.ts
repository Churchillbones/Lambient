import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TranscriptionResponse {
  transcript: string;
}

export interface NoteResponse {
  note: string;
}

export interface NoteRequest {
  transcript: string;
  template?: string;
  api_key?: string;
  endpoint?: string;
  api_version?: string;
  model?: string;
  use_local?: boolean;
  local_model?: string;
  patient_data?: any;
  use_agent_pipeline?: boolean;
  agent_settings?: any;
}

@Injectable({
  providedIn: 'root'
})
export class TranscriptionService {
  private readonly apiUrl = '/api';

  constructor(private http: HttpClient) {}

  transcribeAudio(
    file: File,
    model: string,
    language: string = 'en-US',
    modelPath?: string
  ): Observable<TranscriptionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);
    formData.append('language', language);
    if (modelPath) {
      formData.append('model_path', modelPath);
    }

    return this.http.post<TranscriptionResponse>(`${this.apiUrl}/transcribe`, formData);
  }

  generateNote(request: NoteRequest): Observable<NoteResponse> {
    return this.http.post<NoteResponse>(`${this.apiUrl}/notes`, request);
  }

  getTemplates(): Observable<any> {
    return this.http.get(`${this.apiUrl}/templates`);
  }
}