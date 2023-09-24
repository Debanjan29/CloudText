from django.shortcuts import render,HttpResponse,redirect,HttpResponseRedirect
from . models import Store
from django.contrib import messages
# Create your views here.

import uuid

def generate_unique_id():
    # Generate a random UUID
    unique_id = uuid.uuid4()

    # Extract the first 4 characters to get a 4-digit ID
    return str(unique_id)[:4]

def contains_alphabet(s):
    for char in s:
        if char.isalpha():
            return True
    return False

# Usage example
def create():
  id=generate_unique_id()
  if(contains_alphabet(id)==False) :
    return(id[0:3]+'p')
  else:
    return(id)


def about(request):
    return render(request,"About.html")

def save(request):
    if request.method=="POST":
        msgs=request.POST["content"]
        if msgs==" " or msgs=="" or msgs=="  ":
            return render(request,'save1.html')


        else:
            val=1
            s=create()
            #print(s)
            while(Store.objects.filter(id=s).exists()):
                s=create()
            st=Store(msg=msgs,id=s)
            st.save()
            params={'uuid':s , 'val':val}
            # return redirect('save')
            messages.success(request,"Your unique code is ")
            msgs=''
            return render(request,"save1.html",params)
    
    return render(request,"save1.html")

def get(request):#search
        if request.method=="POST":
            uid=request.POST["query"]
            print(uid)
            val2=1
            param={ 'val2':val2}
            if(len(uid)>6):
                messages.error(request,"Invalid Code")
                return render(request,"save1.html",param)
            else:

                q=Store.objects.filter(id=uid).first()
                param={'msgg':q}
                print(q)
                return render(request,"result1.html",param)
        else:
            return redirect('/')
        