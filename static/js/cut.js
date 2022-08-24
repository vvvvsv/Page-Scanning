DrawingTools =(function(){  
    //公共方法  
    var getDom=function(id){return document.getElementById(id)};  
    var isNull=function(s){return s==undefined||typeof(s)=='undefined'||s==null||s=='null'||s==''||s.length<1};  
    var hideDefRM=function(){document.oncontextmenu=function(){return false}};//屏蔽浏览器默认鼠标事件  
    /**绘图容器*/  
    var cbtCanvas;  
    /**绘图对象*/  
    var cxt;  
    /**绘制的图形列表*/  
    var shapes=new Array();  
    /**编辑的图片的名字*/ 
    var name='';

    var graphkind={'cursor':0,'pen':1,'line':2,'trian':3,'rect':4,'poly':5,'circle':6,'arrow':21,'parallel':41,'trapezoid':42};  
    //背景图片绘制配置  
    var bgPictureConfig={  
            pic:null,//背景图片地址或路径  
            repaint:true,//是否作为永久背景图，每次清除时会进行重绘  
    };   
      
    //绘图基础配置  
    var paintConfig={lineWidth:1,//线条宽度，默认1  
                strokeStyle:'red',//画笔颜色，默认红色  
                fillStyle:'red',//填充色  
                lineJoin:"round",//线条交角样式，默认圆角  
                lineCap:"round",//线条结束样式，默认圆角  
        };  
    //重新载入绘制样式  
    var resetStyle=function(){  
        cxt.strokeStyle=paintConfig.strokeStyle;  
        cxt.lineWidth=paintConfig.lineWidth;  
        cxt.lineJoin=paintConfig.lineJoin;  
        cxt.lineCap=paintConfig.lineCap;  
        cxt.fillStyle=paintConfig.fillStyle;  
    }  
      
    //鼠标图形  
    var cursors=['crosshair','pointer'];  
    /** 切换鼠标样式*/  
    var switchCorser=function(b){  
        cbtCanvas.style.cursor=((isNull(b)?isDrawing():b)?cursors[0]:cursors[1]);  
    }  
    //操作控制变量组  
    var ctrlConfig={  
            kind:0,//当前绘画分类  
            isPainting:false,//是否开始绘制  
            startPoint:null,//起始点  
            cuGraph:null,//当前绘制的图像  
            cuPoint:null,//当前临时坐标点，确定一个坐标点后重新构建  
            cuAngle:null,//当前箭头角度  
            vertex:[],//坐标点  
    }  
    /**获取当前坐标点*/  
    var getCuPoint=function(i){  
        return ctrlConfig.cuPoint[i];  
    }  
    /**设置当前坐标点*/  
    var setCuPoint=function(p,i){  
        return ctrlConfig.cuPoint[i]=p;  
    }  
    /**设置当前临时坐标点值*/  
    var setCuPointXY=function(x,y,i){  
        if(isNull(ctrlConfig.cuPoint)){  
            var arr=new Array();  
            arr[i]=new Point(x,y);  
            ctrlConfig.cuPoint=arr;  
        }else if(isNull(ctrlConfig.cuPoint[i])){  
            setCuPoint(new Point(x,y),i);  
        }else{  
            ctrlConfig.cuPoint[i].setXY(x,y);  
        }  
        return getCuPoint(i);  
    }  
      
    /**是否正在绘制*/  
    var isDrawing=function (){  
        return ctrlConfig.isPainting;  
    }  
    /**开始绘制状态*/  
    var beginDrawing=function(){  
        ctrlConfig.isPainting=true;  
    }  
    /**结束绘制状态*/  
    var stopDrawing=function(){  
        ctrlConfig.isPainting=false;  
    }  
    /**是否有开始坐标点*/  
    var hasStartPoint=function(){  
        return !isNull(ctrlConfig.startPoint);  
    }  
    /**设置当前绘制的图形*/  
    var setCuGraph=function(g){  
         ctrlConfig.cuGraph=g;  
    }  
    /**获取当前绘制的图形*/  
    var getCuGraph=function(){  
        return ctrlConfig.cuGraph;  
    }  
    /**设置开始坐标点（线条的起始点，三角形的顶点，圆形的圆心，四边形的左上角或右下角，多边形的起始点）*/  
    var setStartPoint=function(p){  
        ctrlConfig.startPoint=p;  
    }  
    /**获取开始坐标点*/  
    var getStartPoint=function(){  
        return ctrlConfig.startPoint;  
    }  
      
    /**清空全部*/  
    var clearAll=function(){  
        cxt.clearRect(0,0,cbtCanvas.width,cbtCanvas.height);  
    }  
    /**重绘*/  
    var repaint=function(){  
        clearAll();  
    }  
      
    /**点（坐标,绘图的基本要素,包含x,y坐标）*/  
    var Point=(function(x1,y1){  
        var x=x1,y=y1;  
        return{  
            set:function(p){  
                x=p.x,y=p.y;  
            },  
            setXY:function(x2,y2){  
                x=x2;y=y2;  
            },  
            setX:function(x3){  
                x=x3;  
            },  
            setY:function(y3){  
                y=y3;  
            },  
            getX:function(){  
                return x;  
            },  
            getY:function(){  
                return y;  
            }  
        }  
    });  
    /**多角形（三角形、矩形、多边形），由多个点组成*/  
    var Poly=(function(ps1){  
        var ps=isNull(ps1)?new Array():ps1;  
        var size=0;  
        return{  
            set:function(ps2){  
                ps=ps2;  
            },  
            getSize:function(){  
                return size;  
            },  
            setPoint:function(p,i){  
                if(isNull(p)&&isNaN(i)){  
                    return;  
                }  
                ps[i]=p;  
            },  
            setStart:function(p1){  
                if(isNull(ps)){  
                    ps=new Array();  
                    return ps.push(p1);  
                }else{  
                    ps[0]=p1;  
                }  
            },  
            add:function(p){  
                if(isNull(ps)){  
                    ps=new Array();  
                }
                size++;
                return ps.push(p);  
            },  
            pop:function(){  
                if(isNull(ps)){  
                    return;  
                }  
                return ps.pop();  
            },  
            shift:function(){  
                if(isNull(ps)){  
                    return;  
                }  
                return ps.shift;  
            },  
            get:function(){  
                if(isNull(ps)){  
                    return null;  
                }  
                return ps;  
            },  
            draw:function(){  
                cxt.beginPath();  
                for(i in ps){  
                    if(i==0){  
                        cxt.moveTo(ps[i].getX(),ps[i].getY());  
                    }else{  
                        cxt.lineTo(ps[i].getX(),ps[i].getY());  
                    }  
                }  
                cxt.closePath();  
                cxt.stroke();  
            }  
        }  
    });  
      
    //鼠标按键点击（首次点击确定开始坐标点，拖动鼠标不断进行图形重绘）  
    var mouseDown = function(e){  
        var btnNum = e.button;  
        if(btnNum==0){  
            console.log("选择："+ctrlConfig.kind);  
            //设置起始点  
            switch(ctrlConfig.kind){  
                case graphkind.poly://多边形  
                    var p=new Point(e.offsetX,e.offsetY);  
                    if(isDrawing()){  
                        getCuGraph().add(p);//添加到  
                        // console.log('hhhh'+getCuGraph().getSize())
                        if(getCuGraph().getSize()>=4)
                        {
                            repaint();  
                            getCuGraph().draw(); 
                            ps=getCuGraph().get()
                            for (i in ps)
                                console.log(ps[i].getX()+' '+ps[i].getY()) 
                            stopDrawing();//结束绘制
                            break;
                        }
                    }else{//第一次确定开始坐标  
                        beginDrawing();//开始绘制  
                        setStartPoint(p);  
                        var poly=new Poly();  
                        poly.add(p);  
                        setCuGraph(poly);//设置当前绘制图形  
                    }  
                    break;  
                 case ctrlConfig.cursor: //手型鼠标  
                 default://默认是手型鼠标，不允许绘制  
            }  
        }else if(btnNum==2){  
            console.log("右键由于结束多边形绘制");  
            if(isDrawing()){  
                if(ctrlConfig.kind==graphkind.poly){  
                    repaint();   
                    
                    stopDrawing();//结束绘制  
                }  
            }  
        }  
        hideDefRM();//屏蔽浏览器默认事件  
    }  
    //鼠标移动（拖动，根据鼠标移动的位置不断重绘图形）  
    var mouseMove = function(e){  
        if(isDrawing()&&hasStartPoint()){//检查是否开始绘制，检查是否有开始坐标点  
            //画笔不需要重绘  
            if(ctrlConfig.kind>1){  
                repaint();//重绘  
            }  
            var p=setCuPointXY(e.offsetX,e.offsetY,0);//设置共享的临时坐标点，用于防止重复创建对象  
            switch(ctrlConfig.kind){  
             case graphkind.poly://多边形  
                var poly=getCuGraph();  
                var size=poly.getSize();  
                poly.setPoint(p,-1);  
                poly.draw();  //即时绘制
                break;  
            }  
      }  
    }   
      
    return{  
        isNull:isNull,  
        getDom:getDom,  
        clear:function(){  
            stopDrawing();//停止绘制  
            repaint();  
        },  
        /**初始化*/  
        init:function(params){  
            console.log('will init')
            
            cbtCanvas=getDom(params.id);  
            cxt=cbtCanvas.getContext("2d");
            //浏览器是否支持Canvas  
            if (cxt){  
                /**绘图对象*/  
                cbtCanvas.onmousedown = mouseDown;      
                cbtCanvas.onmousemove = mouseMove;    
                  
                resetStyle();//载入样式  
                return true;  
            }else{  
                return false;  
            }  
            
            
        },   
 
        /**选择图形类型*/  
        begin:function(start){  
            console.log("选择绘制图形："+5);  
            if(isNaN(5)){//如果不是数字，先转换为对应字符  
                ctrlConfig.kind=kind[5];  
            }else{  
                ctrlConfig.kind=5;  
            }  
            switchCorser(true);//切换鼠标样式 
            /*****************************************/ 
            console.log(start)
            name=start[0]
            beginDrawing();
            var poly=new Poly();  
            setCuGraph(poly);//设置当前绘制图形
            for(var i=1;i<start.length;i+=2)
            {
                var p=new Point(start[i],start[i+1]);
                if(i==1) 
                {
                    setStartPoint(p);
                }
                getCuGraph().add(p);
            }
            getCuGraph().draw();
            console.log('draw finished')
            stopDrawing()
            /*****************************************/ 
        },  
        /*手型，并停止绘图*/  
        hand:function(){  
            ctrlConfig.kind=0;  
            stopDrawing();//停止绘制  
            switchCorser(false);//切换鼠标样式  
        },

        result:function(){
            if(!getCuGraph()) return 'none'
            ps=getCuGraph().get()
            res=name+' '
            for (i in ps)
                res+=ps[i].getX()+' '+ps[i].getY()+' '
            return res
        },
        clear:function(){
            repaint();
            cbtCanvas.style.cursor='default'
            cbtCanvas.onmousedown=null
            cbtCanvas.onmousemove=null
            
            return ''
        }
    }  
})  