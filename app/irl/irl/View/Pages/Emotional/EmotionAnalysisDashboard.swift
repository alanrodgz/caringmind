//
//  EmotionAnalysisDashboard.swift
//  irl
//
//  Created by Elijah Arbee on 9/10/24.
//
import SwiftUI

struct EmotionAnalysisDashboard: View {
    @StateObject private var viewModel = EmotionAnalysisViewModel()
    @State private var selectedTab = 0
    
    var body: some View {
        VStack {
            Picker("View", selection: $selectedTab) {
                Text("Overview").tag(0)
                Text("Transcript").tag(1)
                Text("Details").tag(2)
            }
            .pickerStyle(SegmentedPickerStyle())
            .padding()
            
            TabView(selection: $selectedTab) {
                OverviewView(viewModel: viewModel).tag(0)
                EmotionalTranscriptView(viewModel: viewModel).tag(1)
                DetailedAnalysisView(viewModel: viewModel).tag(2)
            }
            .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
        }
        .onAppear {
            viewModel.loadData()
        }
    }
}
